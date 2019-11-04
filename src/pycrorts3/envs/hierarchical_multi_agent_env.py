from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from ..game import Game

NUM_ACTIONS = 9


class HierarchicalPycroRts3MultiAgentEnv(MultiAgentEnv):
    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        map_height = self.game.map.height
        map_width = self.game.map.width

        self.action_space = spaces.Discrete(NUM_ACTIONS)
        self.observation_space = spaces.Dict({
            # 'board': spaces.Box(low=0, high=28, shape=(map_height, map_width), dtype=np.uint8),
            'board': spaces.Box(low=0, high=28, shape=(map_height * map_width,), dtype=np.uint8),
            # 'units': spaces.MultiDiscrete(),
            'num_units': spaces.Box(low=0, high=np.iinfo('uint8').max, shape=(1,), dtype=np.uint8),
            # 'units': spaces.Dict({
            #     # 'id': spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            #     # 'position': spaces.Box(low=0, high=255, shape=(2,), dtype=np.uint8),
            #     # 'type': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            #     # 'hitpoints': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            #     'ids': spaces.MultiDiscrete([1,1]),
            #     'positions': spaces.MultiDiscrete([1,1]),
            # }),
            'player_id': spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
            'resources': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
            'time': spaces.Box(low=0, high=np.iinfo('uint8').max, shape=(1,), dtype=np.uint8),
        })

    def reset(self):
        self.game.reset()
        obs_dict = {}
        for player in self.game.players():
            obs = {
                'board': np.ravel(self.game.get_state()),
                'num_units': np.array([len(self.game.map.units)]),
                'player_id': np.array([player.id]),
                'resources': np.array([player.minerals]),
                'time': np.array([self.game.time]),
            }
            obs_dict[f'high_level_agent_{player.id:02d}'] = obs
        return obs_dict

    def step(self, action_dict):
        obses = {}
        for agent, action in action_dict.items():
            if agent.startswith('high_level_agent'):
                obs = self._high_level_step(action_dict['high_level_agent'])
            else:
                obs = self._low_level_step(action_dict)

        rewards = {self.low_level_agent_id: 0}
        done = {'__all__': False}

        return obses, rewards, done, {}

    def _high_level_step(self, action):
        self.game.update()
        if self.game.is_game_over:
            rewards = {
                self.game.winner: self.game.reward_win,
                1 - self.game.winner: self.game.reward_lose
            }
            done = {'__all__': self.game.is_game_over}
            obs = {}
        else:
            print('High level agent sets goal'.format(action))
            obs = {self.low_level_agent_id: [self.cur_obs, self.current_goal]}
            rewards = {self.low_level_agent_id: 0}
            done = {'__all__': False}

        return obs, rewards, done, {}

    def _low_level_step(self, action_dict):
        print('Low level agent step {}'.format(action_dict))
        for unit_id, action in action_dict.items():
            self.game.step(action)

        obs_dict = {}
        for player in self.game.players():
            obs = {
                'board': np.ravel(self.game.get_state()),
                'num_units': np.array([len(self.game.map.units)]),
                'player_id': np.array([player.id]),
                'resources': np.array([player.minerals]),
                'time': np.array([self.game.time]),
            }
            obs_dict[f'high_level_agent_{player.id:02d}'] = obs

        rewards = {}
        if self.game.is_game_over:
            rewards[self.game.winner] = self.game.reward_win
            rewards[1 - self.game.winner] = self.game.reward_lose

        game_over = {'__all__': self.game.is_game_over}

        return obs_dict, rewards, game_over, {}
