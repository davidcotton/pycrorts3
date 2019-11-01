from enum import Enum

from .position import Position


class Unit:
    # actions = [
    #     'NOOP',
    #     'MOVE_UP',
    #     'MOVE_RIGHT',
    #     'MOVE_DOWN',
    #     'MOVE_LEFT',
    #     'ATTACK_UP',
    #     'ATTACK_RIGHT',
    #     'ATTACK_DOWN',
    #     'ATTACK_LEFT',
    # ]
    actions = [
        'NOOP',
        'MOVE',
        'ATTACK',
        'HARVEST',
        'PRODUCE',
    ]

    def __init__(self,
                 unit_id: int,
                 player_id: int,
                 position: Position,
                 # hitpoints: int,
                 # resources: int,
                 # cost: int,
                 # min_damage: int,
                 # max_damage: int,
                 # attack_range: int,
                 # move_time: int,
                 # harvest_time: int,
                 # # return_time: int,
                 # produce_time: int,
                 # attack_time: int,
                 # sight_radius: int,
                 ) -> None:
        super().__init__()
        self.id = int(unit_id)
        self.player_id = int(player_id)
        self.position: Position = position
        # self.hitpoints = int(hitpoints)
        # self.resources = int(resources)
        # self.cost = int(cost)
        # self.min_damage = int(min_damage)
        # self.max_damage = int(max_damage)
        # self.attack_range = int(attack_range)
        # self.move_time = int(move_time)
        # self.harvest_time = int(harvest_time)
        # # self.return_time = return_time
        # self.produce_time = int(produce_time)
        # self.attack_time = int(attack_time)
        # self.sight_radius = int(sight_radius)

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y


class WorkerUnit(Unit):
    pass


class LightUnit(Unit):
    cost = 2
    hitpoints = 4
    min_damage = 2
    max_damage = 2
    attack_range = 1
    produce_time = 80
    move_time = 8
    attack_time = 5
    sight_radius = 2


class HeavyUnit(Unit):
    pass


class RangedUnit(Unit):
    pass


class BaseBuilding(Unit):
    pass


class BarracksBuilding(Unit):
    pass


unit_type_table = {
    'original': {
        'base': {
            'produce_time': 250,
        },
        'barracks': {

        },
    },
    'fine-tuned': {
        'produce_time': 250,
    },
    'non-deterministic': {},
    'single-move': {},
}


unit_classes = {
    'Worker': WorkerUnit,
    'Light': LightUnit,
    'Heavy': HeavyUnit,
    'Ranged': RangedUnit,
    'Base': BaseBuilding,
    'Barracks': BarracksBuilding,
}


UnitEncoding = Enum('UnitEncoding', 'BaseBuilding BarracksBuilding WorkerUnit LightUnit HeavyUnit RangedUnit')
