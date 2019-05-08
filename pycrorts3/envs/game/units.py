from pycrorts3.envs.game.position import Position


class Unit:

    def __init__(self,
                 unit_id: int,
                 player_id: int,
                 position: Position,
                 hitpoints: int,
                 resources: int,
                 cost: int,
                 min_damage: int,
                 max_damage: int,
                 attack_range: int,
                 move_time: int,
                 harvest_time: int,
                 # return_time: int,
                 produce_time: int,
                 attack_time: int,
                 sight_radius: int,
                 ) -> None:
        super().__init__()
        self.id = int(unit_id)
        self.player_id = int(player_id)
        self.position: Position = position
        self.hitpoints = int(hitpoints)
        self.resources = int(resources)
        self.cost = int(cost)
        self.min_damage = int(min_damage)
        self.max_damage = int(max_damage)
        self.attack_range = int(attack_range)
        self.move_time = int(move_time)
        self.harvest_time = int(harvest_time)
        # self.return_time = return_time
        self.produce_time = int(produce_time)
        self.attack_time = int(attack_time)
        self.sight_radius = int(sight_radius)


class LightUnit(Unit):
    pass


class HeavyUnit(Unit):
    pass


class RangedUnit(Unit):
    pass


class WorkerUnit(Unit):
    pass
