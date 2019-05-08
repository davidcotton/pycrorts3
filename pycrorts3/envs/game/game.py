from typing import Tuple

import numpy as np

from pycrorts3.envs.game.board import Board
from pycrorts3.envs.game.map import Map
from pycrorts3.envs.game.player import Player
from pycrorts3.envs.game.position import Position


class Game:

    def __init__(self) -> None:
        super().__init__()
        # self.board = Board()
        self.map = Map()
        self.players = [Player(i, 0) for i in range(2)]
        self.time = 0
        self.winner = None
        self.is_game_over = False

    def reset(self) -> None:
        self.time = 0
        self.winner = None
        self.is_game_over = False

    def step(self, actions) -> Tuple[np.ndarray, Tuple[float, float], bool, dict]:
        assert not self.is_game_over
        assert len(actions) == 2

        for player, action in enumerate(actions):
            pass

        self.update()

        state = np.array([])
        rewards = (0.0, 0.0)

        self.time += 1

        return state, rewards, self.is_game_over, {}

    def update(self) -> None:
        pass

    def render(self):
        return np.array([])
