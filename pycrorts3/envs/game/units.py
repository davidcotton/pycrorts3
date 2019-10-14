from enum import Enum

from pycrorts3.envs.game.position import Position


# class MicroRTSUnitType(Enum):
#     Resource = 0
#     Base = 1
#     Barracks = 2
#     Worker = 3
#     Light = 4
#     Heavy = 5
#     Ranged = 6


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


# class UnitTypeTable:
#     pass
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


# class UnitFactory:
#     @staticmethod
#     def build(unit_type: str, unit_id: int, player_id: int, position: Position, hitpoints: int, resources: int) -> Unit:
#         if unit_type == 'Resource':
#             cls = ResourceUnit
#             ut = utt.get_type('Resource')
#         elif unit_type == 'Base':
#             cls = BaseUnit
#             ut = utt.get_type('Base')
#         elif unit_type == 'Barracks':
#             cls = BarracksUnit
#             ut = utt.get_type('Barracks')
#         elif unit_type == 'Worker':
#             cls = WorkerUnit
#             ut = utt.get_type('Worker')
#         elif unit_type == 'Light':
#             cls = LightUnit
#             ut = utt.get_type('Light')
#         elif unit_type == 'Heavy':
#             cls = HeavyUnit
#             ut = utt.get_type('Heavy')
#         elif unit_type == 'Ranged':
#             cls = RangedUnit
#             ut = utt.get_type('Ranged')
#         else:
#             raise ValueError
#
#         unit = cls(unit_id, player_id, position, hitpoints, resources, ut.cost, ut.min_damage, ut.max_damage,
#                    ut.attack_range, ut.move_time, ut.harvest_time, ut.return_time, ut.produce_time, ut.attack_time,
#                    ut.sight_radius)
#
#         return unit
