from collections import defaultdict, deque
from typing import List

from .actions import Action, NoopAction, MoveAction, AttackAction
from .map import Map
from .player import Player

MAP_FILENAME = '4x4_melee_light2.xml'
MAX_STEPS_PER_GAME = 1500
REWARD_WIN = 1.0
REWARD_DRAW = 0.5
REWARD_LOSE = 0.0
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
        self.pending_actions = deque()
        self.pending_positions = set()

        # step state
        self.queued_actions = deque()

    def reset(self):
        self.map = Map(self.map_filename())
        self.time = 0
        self.is_game_over = False
        self.winner = None
        self.pending_actions.clear()
        self.pending_positions.clear()
        self.queued_actions.clear()

    def step(self, action):
        # validate action, if invalid replace with NOOP action with same duration
        #  - check terrain & unit positions
        #  - check pending actions
        end_pos = action.position
        if not self.map.is_legal_action(action) or end_pos in self.pending_positions:
            unit = self.map.get_unit(action.unit_id)
            action = NoopAction(action.unit_id, unit.position, action.start_time, action.end_time)
        self.queued_actions.append(action)

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
            end_time = action.end_time
            while len(self.pending_actions) <= end_time:
                self.pending_actions.append([])
            if action.position in self.pending_positions:
                raise ValueError
            assert action.position not in self.pending_positions
            time = end_time - self.time
            self.pending_actions[time].append(action)
            self.pending_positions.add(action.position)
            self.map.get_unit(action.unit_id).in_progress = True

        # 3) execute actions that complete this step
        to_execute = self.pending_actions.popleft()
        for action in to_execute:
            if isinstance(action, NoopAction):
                pass
            elif isinstance(action, MoveAction):
                self.map.move_unit(action.unit_id, action.position)
            elif isinstance(action, AttackAction):
                dead_unit = self.map.attack_unit(action.unit_id, action.position)
                if dead_unit:
                    # copy the microRTS reference implementation
                    # if two units attack simultaneously, the first unit kills the 2nd, before 2nd strikes
                    for step in self.pending_actions:
                        for a in step:
                            if a.unit_id == dead_unit.id:
                                self.pending_positions.remove(a.position)
                    self.map.remove_unit(dead_unit)
            self.pending_positions.remove(action.position)
            self.map.get_unit(action.unit_id).in_progress = False

        # 4) end of episode check & clean up
        self.time += 1
        if self.time >= self.max_steps_per_game():
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
