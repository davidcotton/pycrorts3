from collections import defaultdict, deque
import itertools
from typing import Dict, List

import numpy as np

from .actions import Action, NoopAction, MoveAction, AttackAction, ActionEncodings
from .player import Player
from .state import State
from .units import Unit
from ..game.position import cardinal_to_euclidean

MAP_FILENAME = '4x4_melee_light2.xml'
MAX_STEPS_PER_GAME = 1500
REWARD_WIN = 1.0
REWARD_DRAW = 0.0
REWARD_LOSE = -1.0
REWARD_STEP = 0.0
UTT_VERSION = 2


class Game:
    def __init__(self, env_config=None) -> None:
        super().__init__()

        # config
        # ------
        self.env_config = dict({
            'map_filename': MAP_FILENAME,
            'max_steps_per_game': MAX_STEPS_PER_GAME,
            'reward_win': REWARD_WIN,
            'reward_draw': REWARD_DRAW,
            'reward_lose': REWARD_LOSE,
            'reward_step': REWARD_STEP,
            'utt_version': UTT_VERSION,
        }, **env_config or {})

        # episode state
        # -------------
        self.state = State(self.map_filename())
        self.time = 0
        self.is_game_over = False
        self.winner = None
        # each list of actions in deque represents a game step, indexed from the current step
        self.pending_actions: deque[List[Action]] = deque()

        # step state
        # ----------
        self.queued_actions: deque[Action] = deque()  # action queued to be

    def reset(self) -> None:
        """Reset the game."""
        self.state = State(self.map_filename())
        self.time = 0
        self.is_game_over = False
        self.winner = None
        self.pending_actions.clear()
        self.queued_actions.clear()

    def step(self, action: Action) -> None:
        """Request to make a game action.

        Actions are validated against terrain, current unit positions and `pending` action positions.
        New actions cannot occupy an occupied cell (irrespective of whether the cell could be empty when the action
          executes).
        If the new action is invalid, it will be replaced with a NOOP action of the same duration as the
          original action.
        This copies microRTS logic.

        The original or the replacement NOOP action are then queued to be further processed at the end of the turn,
          during the `update()` method.

        :param action: The action to add.
        """
        if not self.is_legal_action(action):
            unit = self.get_unit(action.unit_id)
            action = NoopAction(action.unit_id, unit.position, action.start_time, action.end_time)
        self.queued_actions.append(action)

    def update(self) -> None:
        """Complete the current game time-step.

        Actions queued this step are validated and added to the queue of pending actions to executed at a later time.

        Invalid actions are replaced with NOOP actions of the same duration as the original action.
        Actions are validated in the order they are received, i.e. 2 valid, queued actions with the same destination,
          the first action will continue as normal, while the second will be replaced with a NOOP.
        Similarly, if two units attack each other simultaneously, the first unit to attack will kill the second unit
          before it has a chance to strike back.
        This is copying microRTS logic.
        """
        assert not self.is_game_over
        # 1) validate queued actions
        #  - count duplicates
        positions = defaultdict(list)
        for i, action in enumerate(self.queued_actions):
            positions[action.position].append(i)
        #  - replace all duplicates with NOOP
        for pos, indexes in positions.items():
            if len(indexes) > 1:
                for i in indexes:
                    action = self.queued_actions[i]
                    start_pos = self.state.units[action.unit_id].position
                    self.queued_actions[i] = NoopAction(action.unit_id, start_pos, action.start_time, action.end_time)

        # 2) move queued actions (this step) to pending (future steps)
        while len(self.queued_actions):
            action = self.queued_actions.popleft()
            relative_end_time = action.end_time - self.time  # relative from now
            while len(self.pending_actions) <= relative_end_time:
                self.pending_actions.append([])
            self.pending_actions[relative_end_time].append(action)
            self.get_unit(action.unit_id).has_pending_action = True

        # 3) execute actions that complete this step
        to_execute = self.pending_actions.popleft()
        while len(to_execute):
            action = to_execute.pop()
            if isinstance(action, NoopAction):
                pass
            elif isinstance(action, MoveAction):
                self.state.move_unit(action.unit_id, action.position)
            elif isinstance(action, AttackAction):
                dead_unit = self.state.attack_unit(action.unit_id, action.position)
                if dead_unit:
                    # copy microRTS logic
                    # if two units attack simultaneously, the first unit kills the 2nd, before 2nd strikes
                    for i, step_actions in enumerate(self.pending_actions):
                        for j, pending_action in enumerate(step_actions):
                            if pending_action.unit_id == dead_unit.id:
                                self.pending_actions[i].pop(j)
                                break
                        else:
                            continue
                        break
                    for i, pending_action in enumerate(to_execute):
                        if pending_action.unit_id == dead_unit.id:
                            if pending_action.unit_id == dead_unit.id:
                                to_execute.pop(i)
                                break
                    self.state.remove_unit(dead_unit.id)
                    # check player has units
                    num_units = sum(1 if u.player_id == dead_unit.player_id else 0 for u in self.state.units.values() if
                                    not u.is_dead())
                    if num_units == 0:
                        self.is_game_over = True
                        self.winner = 1 - dead_unit.player_id
                        print('GAME OVER, winner: %s' % self.winner)
                        return  # abort updating, game over
            self.get_unit(action.unit_id).has_pending_action = False

        # 4) end of episode check & clean up
        self.time += 1
        if self.time >= self.max_steps_per_game:
            print('GAME OVER, draw')
            self.is_game_over = True

    def is_legal_action(self, action: Action) -> bool:
        """Determine if an action is consistent with in the current game state.

        :param action: The action to check.
        :return: True if the action is valid, else False.
        """
        future_actions = list(itertools.chain(*self.pending_actions))
        future_actions += self.queued_actions
        for other in future_actions:
            if action.unit_id == other.unit_id:
                return False  # an action already in-progress for this unit
            if isinstance(action, MoveAction):
                if action.position == other.position:
                    return False  # square _might_ be occupied when the action executes (copying microRTS logic)
        is_valid = self.state.is_legal_action(action)
        return is_valid

    def get_action_mask(self, unit: Unit):
        """Get a mask of legal actions available to a unit.

        :param unit: The unit to generate the action mask for.
        :return: A numpy array where 1 is a legal action, else 0
        """
        if unit.has_pending_action or unit.is_dead():
            action_mask = np.zeros(shape=(len(ActionEncodings),), dtype=np.uint8)
            action_mask[0] = 1
            return action_mask

        future_actions = list(itertools.chain(*self.pending_actions))
        future_actions += self.queued_actions
        action_mask = self.state.get_action_mask(unit)
        # mask move actions set to be occupied by other pending actions
        for action_id in range(1, 5):
            if action_mask[action_id] == 0:
                continue
            action_type = ActionEncodings(action_id).name
            position = cardinal_to_euclidean(unit.position, action_type)
            for other in future_actions:
                if position == other.position:
                    action_mask[action_id] = 0

        return action_mask

    def get_state(self, unit_id: int):
        """Get a representation of the game state from a unit's perspective.

        :param unit_id: The ID of the unit to fetch the state for.
        :return: A numpy array encoded to represent the state.
        """
        return self.state.to_array(unit_id)

    @property
    def players(self) -> List[Player]:
        return self.state.players

    @property
    def units(self) -> Dict[int, Unit]:
        return self.state.units

    def get_unit(self, unit_id: int) -> Unit:
        return self.state.get_unit(unit_id)

    def map_filename(self) -> str:
        return self.env_config['map_filename']

    def height(self) -> int:
        return self.state.height

    def width(self) -> int:
        return self.state.width

    @property
    def max_steps_per_game(self) -> int:
        return self.env_config['max_steps_per_game']

    def reward_win(self) -> float:
        return self.env_config['reward_win']

    def reward_draw(self) -> float:
        return self.env_config['reward_draw']

    def reward_lose(self) -> float:
        return self.env_config['reward_lose']

    def reward_step(self) -> float:
        return self.env_config['reward_step']

    def utt_version(self) -> int:
        return self.env_config['utt_version']
