from typing import Tuple

import gym
from gym import spaces
import numpy as np

from ..game import Game
from ..game import Actions


class PycroRts3Env(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        map_height = self.game.map.height
        map_width = self.game.map.width
        self.action_space = spaces.Discrete(len(Actions))
        self.observation_space = spaces.Box(low=0, high=255, shape=(map_height, map_width), dtype=np.uint8)
        self.time = 0
        self.game_over = False
        self.winner = None

    def reset(self) -> np.ndarray:
        self.time = 0
        self.game_over = False
        self.winner = None

        # state = self.game.reset()
        state = self.map[:]

        return state

    def step(self, action) -> Tuple[np.ndarray, float, bool, dict]:
        # return self.game.step(action)
        next_state = self.map[:]
        reward = 0.0

        return next_state, reward, self.game_over, {}

    def render(self, mode='human') -> None:
        print('foo')
        # self.game.render()
