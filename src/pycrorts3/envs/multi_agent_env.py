from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from ..game import Game
from ..game.actions import ActionEncodings, NoopAction, MoveAction, AttackAction
from ..game.position import cardinal_to_euclidean

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
            # 'board': spaces.Box(low=0, high=28, shape=(map_height, map_width), dtype=np.uint8),
            'board': spaces.Box(low=0, high=28, shape=(map_height * map_width,), dtype=np.uint8),
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
        for unit_id, unit in self.game.map.units.items():
            player_id = unit.player_id
            obs = {
                'action_mask': self.game.map.get_action_mask(unit),
                'board': np.ravel(self.game.get_state(unit_id)),
                'player_id': np.array([player_id]),
                'resources': np.array([self.game.map.players[player_id].minerals]),
                'time': np.array([self.game.time]),
            }
            obs_dict[unit_id] = obs
        return obs_dict

    def step(self, action_dict):
        # convert action indexes into game action objects and queue them
        for unit_id, action_id in action_dict.items():
            unit = self.game.map.get_unit(unit_id)
            if unit.in_progress:
                continue
            action_type = ActionEncodings(action_id).name
            start_time = self.game.time
            if action_type == 'NOOP':
                end_time = self.game.time
                action = NoopAction(unit_id, unit.position, start_time, end_time)
            elif action_type.startswith('MOVE'):
                pos = cardinal_to_euclidean(unit.position, action_type)
                end_time = self.game.time + unit.move_time - 1
                action = MoveAction(unit_id, pos, start_time, end_time)
            elif action_type.startswith('ATTACK'):
                pos = cardinal_to_euclidean(unit.position, action_type)
                end_time = self.game.time + unit.attack_time - 1
                action = AttackAction(unit_id, pos, start_time, end_time)
            else:
                raise ValueError('Invalid action')
            self.game.step(action)

        # update the game with actions begun & completed this step
        self.game.update()

        # generate the return values, <obs, rew, done, info>
        obs_dict = {}
        rewards = {}
        for unit_id, unit in self.game.map.units.items():
            player_id = unit.player_id
            obs = {
                'action_mask': self.game.map.get_action_mask(unit),
                'board': np.ravel(self.game.get_state(unit_id)),
                'player_id': np.array([player_id]),
                'resources': np.array([self.game.map.players[player_id].minerals]),
                'time': np.array([self.game.time]),
            }
            obs_dict[unit_id] = obs

            if self.game.is_game_over:
                if unit.player_id == self.game.winner:
                    reward = self.game.reward_win()
                elif (1 - unit.player_id) == self.game.winner:
                    reward = self.game.reward_lose()
                else:
                    reward = self.game.reward_draw()
                rewards[unit_id] = reward
            else:
                rewards[unit_id] = self.game.reward_step()

        game_over = {'__all__': self.game.is_game_over}

        return obs_dict, rewards, game_over, {}
