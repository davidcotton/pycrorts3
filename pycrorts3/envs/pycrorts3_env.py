from typing import Tuple

import gym
from gym import spaces
import numpy as np

from pycrorts3.envs.game.game import Game
from pycrorts3.envs.game.actions import Actions


BOARD_WIDTH = 8
BOARD_HEIGHT = 8


class PycroRts3Env(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self) -> None:
        super().__init__()
        self.action_space = spaces.Discrete(len(Actions))
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(BOARD_HEIGHT, BOARD_WIDTH),
            dtype=np.uint8
        )
        self.time = 0
        self.game_over = False
        self.winner = None
        # self.game = Game()
        self.map = np.zeros((BOARD_HEIGHT, BOARD_WIDTH), dtype=np.uint8)

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
