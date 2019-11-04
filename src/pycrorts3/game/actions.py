from enum import Enum

from .position import Position
from .units import Unit


ActionTypes = Enum(
    'ActionTypes',
    ['NoopAction', 'MoveAction', 'AttackAction', 'HarvestAction', 'ProduceAction'],
    start=0
)
ActionEncodings = Enum(
    'ActionEncodings',
    ['NOOP', 'MOVE_UP', 'MOVE_RIGHT', 'MOVE_DOWN', 'MOVE_LEFT', 'ATTACK_UP', 'ATTACK_RIGHT', 'ATTACK_DOWN',
     'ATTACK_LEFT'],
    start=0
)


class Action:
    def __init__(self, unit_id, position, start_time, end_time) -> None:
        super().__init__()
        self.unit_id = unit_id
        self.position = position
        self.start_time = start_time
        self.end_time = end_time


class NoopAction(Action):
    pass


class MoveAction(Action):
    pass


class AttackAction(Action):
    pass


class HarvestAction(Action):
    pass


class ProduceAction(Action):
    pass


action_encoding_classes = {
    ActionEncodings.NOOP: NoopAction,
    ActionEncodings.MOVE_UP: MoveAction,
    ActionEncodings.MOVE_RIGHT: MoveAction,
    ActionEncodings.MOVE_DOWN: MoveAction,
    ActionEncodings.MOVE_LEFT: MoveAction,
    ActionEncodings.ATTACK_UP: AttackAction,
    ActionEncodings.ATTACK_RIGHT: AttackAction,
    ActionEncodings.ATTACK_DOWN: AttackAction,
    ActionEncodings.ATTACK_LEFT: AttackAction,
}
