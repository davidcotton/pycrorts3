from gym import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from ..game import Game
from ..game.actions import ActionEncodings, NoopAction, MoveAction, AttackAction, HarvestAction, ReturnAction, \
    ProduceAction
from ..game.position import cardinal_to_euclidean
from ..game.units import Resource, unit_produces

num_actions = len(ActionEncodings)


class PycroRts3MultiAgentEnv(MultiAgentEnv):
    def __init__(self, env_config=None) -> None:
        super().__init__()
        self.game = Game(env_config)
        self.action_space = self._act_space()
        self.observation_space = self._obs_space()

    def _act_space(self) -> spaces.Space:
        return spaces.Discrete(num_actions)

    # def _obs_space(self) -> spaces.Space:
    #     return spaces.Dict({
    #         'action_mask': spaces.Box(low=0, high=1, shape=(num_actions,), dtype=np.uint8),
    #         'board': spaces.Box(low=0, high=28, shape=(self.game.height() * self.game.width(),), dtype=np.uint8),
    #         # 'units': spaces.Dict({
    #         #     # 'id': spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
    #         #     # 'position': spaces.Box(low=0, high=255, shape=(2,), dtype=np.uint8),
    #         #     # 'type': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
    #         #     # 'hitpoints': spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
    #         #     'ids': spaces.MultiDiscrete([1,1]),
    #         #     'positions': spaces.MultiDiscrete([1,1]),
    #         # }),
    #         'player_id': spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
    #         'unit_id': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
    #         'resources': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
    #         'time': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
    #     })

    def _obs_space(self) -> spaces.Space:
        return spaces.Dict({
            'action_mask': spaces.Box(low=0, high=1, shape=(num_actions,), dtype=np.uint8),
            # 'avail_actions': spaces.Box(-10, 10, shape=(num_actions, 2)),
            'board': spaces.Box(low=0, high=28, shape=(self.game.height() * self.game.width(),), dtype=np.uint8),
            # 'player_id': spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
            # 'unit_id': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
            # 'resources': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
            # 'time': spaces.Box(low=0, high=np.iinfo('uint16').max, shape=(1,), dtype=np.uint16),
        })

    def reset(self):
        self.game.reset()
        obs_dict = {}
        for unit in self.game.units.values():
            if isinstance(unit, Resource):
                continue  # don't build observations for minerals
            agent_id = f'{unit.player_id}.{unit.id}'
            obs_dict[agent_id] = {
                'action_mask': self.game.get_action_mask(unit),
                'board': self._get_board(unit.id),
                # 'player_id': np.array([unit.player_id]),
                # 'unit_id': np.array([unit.id]),
                # 'resources': np.array([self.game.players[unit.player_id].minerals]),
                # 'time': np.array([self.game.time]),
            }
        return obs_dict

    def step(self, action_dict):
        # convert action indexes into game action objects and enqueue
        for agent_id, action_id in action_dict.items():
            player_id, unit_id = [int(x) for x in agent_id.split('.')]
            unit = self.game.get_unit(unit_id)
            action_type = ActionEncodings(action_id).name
            start_time = self.game.time
            if action_type == 'NOOP':
                end_time = self.game.time
                action = NoopAction(unit_id, unit.position, start_time, end_time)
            else:
                position = cardinal_to_euclidean(unit.position, action_type)
                if action_type.startswith('MOVE'):
                    end_time = self.game.time + unit.move_time - 1
                    action = MoveAction(unit_id, position, start_time, end_time)
                elif action_type.startswith('ATTACK'):
                    end_time = self.game.time + unit.attack_time - 1
                    # for target in self.game.units.values():
                    #     if target.position == position:
                    #         break
                    # else:
                    #     raise ValueError
                    # action = AttackAction(unit_id, position, start_time, end_time, target.id)
                    action = AttackAction(unit_id, position, start_time, end_time)
                elif action_type.startswith('HARVEST'):
                    end_time = self.game.time + unit.harvest_time - 1
                    action = HarvestAction(unit_id, position, start_time, end_time)
                elif action_type.startswith('RETURN'):
                    end_time = self.game.time + unit.return_time - 1
                    action = ReturnAction(unit_id, position, start_time, end_time)
                elif action_type.startswith('PRODUCE'):
                    produces = unit_produces[unit.__class__]
                    produce_type = produces[0]
                    end_time = self.game.time + produce_type.produce_time - 1
                    action = ProduceAction(unit_id, position, start_time, end_time, produce_type)
                else:
                    raise ValueError('Invalid action')
            self.game.step(action)

        # update the game with actions begun & completed this step
        self.game.update()

        # generate the return values, <obs, rew, done, info>
        obs_dict = {}
        rewards = {}
        for unit in self.game.units.values():
            if isinstance(unit, Resource):
                continue  # don't build observations for minerals
            if not unit.can_make_action() and not self.game.is_game_over:
                # units must finish an action before starting a new one
                # unless the game is over, in which case we must send RLlib terminal obs+rewards or else it gets angry
                continue
            agent_id = f'{unit.player_id}.{unit.id}'
            obs_dict[agent_id] = {
                'action_mask': self.game.get_action_mask(unit),
                'board': self._get_board(unit.id),
                # 'player_id': np.array([unit.player_id]),
                # 'unit_id': np.array([unit.id]),
                # 'resources': np.array([self.game.players[unit.player_id].minerals]),
                # 'time': np.array([self.game.time]),
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
