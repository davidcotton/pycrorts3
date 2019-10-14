from typing import Dict, Tuple

import numpy as np

from pycrorts3.envs.game.map import Map
from pycrorts3.envs.game.player import Player
from pycrorts3.envs.game.position import Position
from pycrorts3.envs.game.units import Unit


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
        self.env_config = dict({
            'map_filename': MAP_FILENAME,
            'max_steps_per_game': MAX_STEPS_PER_GAME,
            'reward_win': REWARD_WIN,
            'reward_draw': REWARD_DRAW,
            'reward_lose': REWARD_LOSE,
            'reward_step': REWARD_STEP,
            'utt_version': UTT_VERSION,
        }, **env_config or {})

        self.map = Map(self.map_filename)
        self.time = 0
        self.is_game_over = False
        self.winner = None

    def reset(self):
        self.map = Map(self.map_filename)
        self.time = 0
        self.is_game_over = False
        self.winner = None

    def step(self, action):
        assert not self.is_game_over

    def update(self) -> None:
        pass

    def get_state(self, unit_id):
        return self.map.get_state(unit_id)

    @property
    def map_filename(self) -> str:
        return self.env_config['map_filename']

    @property
    def max_steps_per_game(self) -> int:
        return self.env_config['max_steps_per_game']

    @property
    def reward_win(self) -> float:
        return self.env_config['reward_win']

    @property
    def reward_draw(self) -> float:
        return self.env_config['reward_draw']

    @property
    def reward_lose(self) -> float:
        return self.env_config['reward_lose']

    @property
    def reward_step(self) -> float:
        return self.env_config['reward_step']

    @property
    def utt_version(self) -> int:
        return self.env_config['utt_version']
