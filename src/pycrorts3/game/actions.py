from enum import Enum

from .units import Unit


class Actions(Enum):
    NoopAction = 0
    MoveAction = 1
    AttackAction = 2
    HarvestAction = 3
    ProduceAction = 4


class Action:
    def __init__(self, unit: Unit) -> None:
        super().__init__()
        self.unit: Unit = unit


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
