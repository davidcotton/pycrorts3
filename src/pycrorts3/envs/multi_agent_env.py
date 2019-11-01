from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from ..game import Game

NUM_ACTIONS = 9


class PycroRts3MultiAgentEnv(MultiAgentEnv):
    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        map_height = self.game.map.height
        map_width = self.game.map.width

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
            # 'resources': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(2,), dtype=np.uint16),
        })

    def reset(self):
        self.game.reset()
        obs_dict = {}
        for unit in self.game.map.units.values():
            obs = {
                'action_mask': np.ones((NUM_ACTIONS,), dtype=np.uint8),
                'terrain': self.game.map.get_state(unit.id),
                'player_id': np.array([unit.player_id]),
                # 'resources': [],
            }
            obs_dict[unit.id] = obs
        return obs_dict

    def step(self, action_dict):
        for unit_id, action in action_dict.items():
            self.game.step(action)

        self.game.update()

        obs_dict = {}
        for unit in self.game.map.units.values():
            obs_dict[unit.id] = {
                'action_mask': np.ones((NUM_ACTIONS,), dtype=np.uint8),
                'terrain': self.game.map.get_state(unit.id),
                'player_id': np.array([unit.player_id]),
                # 'resources': self._get_resources(),
            }

        rewards = {}
        if self.game.is_game_over:
            rewards[self.game.winner] = self.game.reward_win
            rewards[1 - self.game.winner] = self.game.reward_lose

        game_over = {'__all__': self.game.is_game_over}

        return obs_dict, rewards, game_over, {}
