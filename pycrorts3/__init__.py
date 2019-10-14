import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

register(
    id='PycroRTSEnv-v3',
    entry_point='pycrorts3.envs:PycroRts3Env',
)

register(
    id='PycroRTSMultiAgentEnv-v3',
    entry_point='pycrorts3.envs:PycroRts3MultiAgentEnv',
)
