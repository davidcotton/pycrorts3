from enum import Enum

from .position import Position


ActionTypes = Enum(
    'ActionTypes',
    ['NoopAction', 'MoveAction', 'AttackAction', 'HarvestAction', 'ReturnAction', 'ProduceAction'],
    start=0
)
ActionEncodings = Enum(
    'ActionEncodings',
    ['NOOP',
     'MOVE_UP', 'MOVE_RIGHT', 'MOVE_DOWN', 'MOVE_LEFT',
     'ATTACK_UP', 'ATTACK_RIGHT', 'ATTACK_DOWN', 'ATTACK_LEFT',
     'HARVEST_UP', 'HARVEST_RIGHT', 'HARVEST_DOWN', 'HARVEST_LEFT',
     'RETURN_UP', 'RETURN_RIGHT', 'RETURN_DOWN', 'RETURN_LEFT',
     # 'PRODUCE_UP', 'PRODUCE_RIGHT', 'PRODUCE_DOWN', 'PRODUCE_LEFT'
     ],
    start=0
)


class Action:
    def __init__(self, unit_id: int, position: Position, start_time: int, end_time: int) -> None:
        super().__init__()
        self.unit_id = int(unit_id)
        self.position = position
        self.start_time = int(start_time)
        self.end_time = int(end_time)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__[:-6]}<unit:{self.unit_id}, pos:({self.position.x}, {self.position.y})>'


class NoopAction(Action):
    pass


class MoveAction(Action):
    pass


class AttackAction(Action):
    pass
    # def __init__(self, unit_id: int, position: Position, start_time: int, end_time: int, target_id: int) -> None:
    #     super().__init__(unit_id, position, start_time, end_time)
    #     self.target_id = target_id


class HarvestAction(Action):
    pass
    # def __init__(self, unit_id: int, position: Position, start_time: int, end_time: int, target_id: int) -> None:
    #     super().__init__(unit_id, position, start_time, end_time)
    #     self.target_id = target_id


class ReturnAction(Action):
    pass
    # def __init__(self, unit_id: int, position: Position, start_time: int, end_time: int, target_id: int) -> None:
    #     super().__init__(unit_id, position, start_time, end_time)
    #     self.target_id = target_id


class ProduceAction(Action):
    def __init__(self, unit_id, position, start_time, end_time, produce_type) -> None:
        super().__init__(unit_id, position, start_time, end_time)
        self.produce_type = produce_type


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
    ActionEncodings.HARVEST_UP: HarvestAction,
    ActionEncodings.HARVEST_RIGHT: HarvestAction,
    ActionEncodings.HARVEST_DOWN: HarvestAction,
    ActionEncodings.HARVEST_LEFT: HarvestAction,
    ActionEncodings.RETURN_UP: ReturnAction,
    ActionEncodings.RETURN_RIGHT: ReturnAction,
    ActionEncodings.RETURN_DOWN: ReturnAction,
    ActionEncodings.RETURN_LEFT: ReturnAction,
    # ActionEncodings.PRODUCE_UP: ProduceAction,
    # ActionEncodings.PRODUCE_RIGHT: ProduceAction,
    # ActionEncodings.PRODUCE_DOWN: ProduceAction,
    # ActionEncodings.PRODUCE_LEFT: ProduceAction,
}
