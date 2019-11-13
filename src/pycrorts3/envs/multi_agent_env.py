from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from ..game import Game
from ..game.actions import ActionEncodings, NoopAction, MoveAction, AttackAction
from ..game.position import cardinal_to_euclidean

num_actions = len(ActionEncodings)


class PycroRts3MultiAgentEnv(MultiAgentEnv):
    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        self.action_space = self._act_space()
        self.observation_space = self._obs_space()

    def _act_space(self) -> spaces.Space:
        return spaces.Discrete(num_actions)

    def _obs_space(self) -> spaces.Space:
        return spaces.Dict({
            'action_mask': spaces.Box(low=0, high=1, shape=(num_actions,), dtype=np.uint8),
            'board': spaces.Box(low=0, high=28, shape=(self.game.height() * self.game.width(),), dtype=np.uint8),
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
            'time': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
        })

    def reset(self):
        self.game.reset()
        obs_dict = {}
        for unit_id, unit in self.game.units.items():
            player_id = unit.player_id
            agent_id = f'{player_id}.{unit_id}'
            obs_dict[agent_id] = {
                'action_mask': self.game.get_action_mask(unit),
                'board': self._get_board(unit_id),
                'player_id': np.array([player_id]),
                'resources': np.array([self.game.players[player_id].minerals]),
                'time': np.array([self.game.time]),
            }
        return obs_dict

    def step(self, action_dict):
        # convert action indexes into game action objects and queue them
        for agent_id, action_id in action_dict.items():
            player_id, unit_id = [int(x) for x in agent_id.split('.')]
            unit = self.game.get_unit(unit_id)
            if unit.has_pending_action:
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
        for unit_id, unit in self.game.units.items():
            player_id = unit.player_id
            agent_id = f'{player_id}.{unit_id}'
            obs_dict[agent_id] = {
                'action_mask': self.game.get_action_mask(unit),
                'board': self._get_board(unit_id),
                'player_id': np.array([player_id]),
                'resources': np.array([self.game.players[player_id].minerals]),
                'time': np.array([self.game.time]),
            }

            if self.game.is_game_over:
                if unit.player_id == self.game.winner:
                    reward = self.game.reward_win()
                elif (1 - unit.player_id) == self.game.winner:
                    reward = self.game.reward_lose()
                else:
                    reward = self.game.reward_draw()
            else:
                reward = self.game.reward_step()
            rewards[agent_id] = reward

        game_over = {'__all__': self.game.is_game_over}

        return obs_dict, rewards, game_over, {}

    def _get_board(self, unit_id: int) -> np.array:
        return np.ravel(self.game.get_state(unit_id))


class SquarePycroRts3MultiAgentEnv(PycroRts3MultiAgentEnv):
    def _obs_space(self) -> spaces.Space:
        return spaces.Dict({
            'action_mask': spaces.Box(low=0, high=1, shape=(num_actions,), dtype=np.uint8),
            'board': spaces.Box(low=0, high=28, shape=(self.game.height(), self.game.width()), dtype=np.uint8),
            'player_id': spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
            'resources': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
            'time': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
        })

    def _get_board(self, unit_id: int) -> np.array:
        return self.game.get_state(unit_id)
