import logging

from gym.envs.registration import register

from .envs.multi_agent_env import PycroRts3MultiAgentEnv


logger = logging.getLogger(__name__)

register(
    id='PycroRTSEnv-v3',
    entry_point='pycrorts3.envs:PycroRts3Env',
)
