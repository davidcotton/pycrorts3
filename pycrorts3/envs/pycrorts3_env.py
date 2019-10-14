from typing import Tuple

import gym
from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from pycrorts3.envs.game.game import Game
from pycrorts3.envs.game.actions import Actions

NUM_ACTIONS = 9


class PycroRts3Env(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
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


class PycroRts3MultiAgentEnv(MultiAgentEnv):
    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        map_height = self.game.map_height
        map_width = self.game.map_width

        self.action_space = spaces.Discrete(NUM_ACTIONS)
        self.observation_space = spaces.Dict({
            'action_mask': spaces.Box(low=0, high=1, shape=(NUM_ACTIONS,), dtype=np.uint8),
            'terrain': spaces.Box(low=0, high=28, shape=(map_height, map_width), dtype=np.uint8),
            # 'units': spaces.Dict({
            #     # 'id': spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            #     # 'position': spaces.Box(low=0, high=255, shape=(2,), dtype=np.uint8),
            #     # 'type': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            #     # 'hitpoints': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            #     'ids': spaces.MultiDiscrete([1,1]),
            #     'positions': spaces.MultiDiscrete([1,1]),
            # }),
            'player_id': spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
            # 'resources': spaces.Box(low=0, high=65535, shape=(2,), dtype=np.uint16),
        })

    def reset(self):
        self.game.reset()
        obs_dict = {}
        for unit in self.game.map.units.values():
            # if unit.player_id == 0:
            obs = {
                'action_mask': np.ones((NUM_ACTIONS,), dtype=np.uint8),
                'terrain': np.zeros((self.game.map.height, self.game.map.width), dtype=np.uint8),
                'player_id': np.array([unit.player_id]),
                # 'resources': [],
            }
            obs_dict[unit.id] = obs
        return obs_dict

    def step(self, action_dict):
        obs_dict = {}
        rewards = {}
        for player, actions in action_dict.items():
            new_obs, reward, game_over, _ = self.game.step(actions)
            obs_dict[player] = {
                'action_mask': self.get_action_mask(player),
                # 'terrain': self.game.terrain,
                # 'units': self._get_units(player),
                'board': self._get_board(player),
                'player_id': np.array([player]),
                'resources': self._get_resources(),
            }
            rewards[player] = reward
        game_over = {'__all__': self.game.is_game_over}
        return obs_dict, rewards, game_over, {}
