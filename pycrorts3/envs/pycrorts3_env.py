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
            shape=(BOARD_HEIGHT, BOARD_WIDTH, 3),
            dtype=np.uint8
        )
        # self.time = 0
        # self.game_over = False
        # self.winner = None
        self.game = Game()

    def reset(self):
        # self.time = 0
        # self.game_over = False
        # self.winner = None
        self.game.reset()

    def step(self, action):
        return self.game.step(action)

    def render(self, mode='human'):
        return self.game.render()
