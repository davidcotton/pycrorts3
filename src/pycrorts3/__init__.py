import logging

from gym.envs.registration import register

from .envs import PycroRts3MultiAgentEnv, HierarchicalPycroRts3MultiAgentEnv


logger = logging.getLogger(__name__)

register(
    id='PycroRTSEnv-v3',
    entry_point='pycrorts3.envs:PycroRts3Env',
)
