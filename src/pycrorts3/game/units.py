from enum import Enum

from .position import Position


class Unit:
    cost = 0
    hitpoints = 0
    min_damage = 0
    max_damage = 0
    attack_range = 0
    produce_time = 0
    move_time = 0
    attack_time = 0
    harvest_time = 0
    return_time = 0
    sight_radius = 0

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
        self.in_progress = False

    @property
    def x(self) -> int:
        return self.position.x

    @property
    def y(self) -> int:
        return self.position.y

    def deal_damage(self, deterministic=True) -> int:
        if deterministic:
            return self.max_damage
        else:
            return self.max_damage  # todo

    def is_dead(self) -> bool:
        return self.hitpoints <= 0

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.position.x},{self.position.y}>'


class WorkerUnit(Unit):
    cost = 1
    hitpoints = 1
    min_damage = 1
    max_damage = 1
    attack_range = 1
    produce_time = 50
    move_time = 10
    attack_time = 5
    harvest_time = 20
    return_time = 10
    sight_radius = 3


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
    cost = 3
    hitpoints = 8
    min_damage = 4
    max_damage = 4
    attack_range = 1
    produce_time = 120
    move_time = 10
    attack_time = 5
    sight_radius = 2


class RangedUnit(Unit):
    cost = 2
    hitpoints = 1
    min_damage = 1
    max_damage = 1
    attack_range = 3
    produce_time = 100
    move_time = 10
    attack_time = 5
    sight_radius = 3


class BaseBuilding(Unit):
    cost = 10
    hitpoints = 10
    min_damage = 0
    max_damage = 0
    attack_range = 0
    produce_time = 200
    move_time = 0
    attack_time = 0
    sight_radius = 5


class BarracksBuilding(Unit):
    cost = 5
    hitpoints = 4
    min_damage = 0
    max_damage = 0
    attack_range = 0
    produce_time = 200
    move_time = 0
    attack_time = 0
    sight_radius = 3


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
