from collections import defaultdict, deque
import itertools
from typing import List

import numpy as np

from .actions import Action, NoopAction, MoveAction, AttackAction, ActionEncodings
from .map import Map
from .player import Player
from ..game.position import cardinal_to_euclidean
from .units import Unit

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
        self.map = Map(self.map_filename())
        self.time = 0
        self.is_game_over = False
        self.winner = None
        self.pending_actions: deque[Action] = deque()

        # step state
        self.queued_actions: deque[Action] = deque()

    def reset(self):
        self.map = Map(self.map_filename())
        self.time = 0
        self.is_game_over = False
        self.winner = None
        self.pending_actions.clear()
        self.queued_actions.clear()

    def step(self, action):
        # validate action, if invalid replace with NOOP action with same duration
        #  - check terrain & unit positions
        #  - check pending actions
        if not self.is_legal_action(action):
            unit = self.map.get_unit(action.unit_id)
            action = NoopAction(action.unit_id, unit.position, action.start_time, action.end_time)
        # queue the action to be processed at the end of turn
        self.queued_actions.append(action)

    def is_legal_action(self, action):
        future_actions = list(itertools.chain(*self.pending_actions))
        future_actions += self.queued_actions
        for other in future_actions:
            if action.unit_id == other.unit_id:
                return False  # an action already in-progress for this unit
            if isinstance(action, MoveAction):
                if action.position == other.position:
                    return False  # square _might_ be occupied when the action executes (copying microRTS logic)
        is_valid = self.map.is_legal_action(action)
        return is_valid

    def get_action_mask(self, unit: Unit):
        if unit.is_dead():
            action_mask = np.zeros(shape=(len(ActionEncodings),), dtype=np.uint8)
            action_mask[0] = 1
            return action_mask

        future_actions = list(itertools.chain(*self.pending_actions))
        future_actions += self.queued_actions
        for action in future_actions:
            if action.unit_id == unit.id:
                # target unit has an action in-progress, can't make any legal actions
                action_mask = np.zeros(shape=(len(ActionEncodings),), dtype=np.uint8)
                action_mask[0] = 1  # use NOOP until we add in-progress flag to action mask
                break
        else:
            action_mask = self.map.get_action_mask(unit)
            # mask move directions set to be occupied by other pending actions
            for action_id in range(1, 5):
                if action_mask[action_id] == 0:
                    continue
                action_type = ActionEncodings(action_id).name
                position = cardinal_to_euclidean(unit.position, action_type)
                for other in future_actions:
                    if position == other.position:
                        action_mask[action_id] = 0

        return action_mask

    def update(self) -> None:
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
                    start_pos = self.map.units[action.unit_id].position
                    self.queued_actions[i] = NoopAction(action.unit_id, start_pos, action.start_time, action.end_time)

        # 2) move queued actions (this step) to pending (future steps)
        while len(self.queued_actions):
            action = self.queued_actions.popleft()
            relative_end_time = action.end_time - self.time  # relative from now
            while len(self.pending_actions) <= relative_end_time:
                self.pending_actions.append([])
            self.pending_actions[relative_end_time].append(action)
            self.map.get_unit(action.unit_id).in_progress = True

        # 3) execute actions that complete this step
        to_execute = self.pending_actions.popleft()
        while len(to_execute):
            action = to_execute.pop()
            if isinstance(action, NoopAction):
                pass
            elif isinstance(action, MoveAction):
                self.map.move_unit(action.unit_id, action.position)
            elif isinstance(action, AttackAction):
                dead_unit = self.map.attack_unit(action.unit_id, action.position)
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
                    self.map.remove_unit(dead_unit.id)
                    # check player has units
                    num_units = sum(1 if u.player_id == dead_unit.player_id else 0 for u in self.map.units.values() if
                                    not u.is_dead())
                    if num_units == 0:
                        self.is_game_over = True
                        self.winner = 1 - dead_unit.player_id
                        print('GAME OVER, winner: %s' % self.winner)
                        return  # abort updating, game over
            self.map.get_unit(action.unit_id).in_progress = False

        # 4) end of episode check & clean up
        self.time += 1
        if self.time >= self.max_steps_per_game():
            print('GAME OVER, draw')
            self.is_game_over = True

    def get_state(self, unit_id=None):
        return self.map.to_array(unit_id)

    def players(self) -> List[Player]:
        return self.map.players

    def map_filename(self) -> str:
        return self.env_config['map_filename']

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
