import os

import numpy as np
import untangle

from pycrorts3.envs.game.player import Player
from pycrorts3.envs.game.position import Position
from pycrorts3.envs.game.units import Unit, unit_classes, UnitEncoding


class Map:
    def __init__(self, map_filename) -> None:
        super().__init__()
        map_data = self._read_map_file(map_filename)

        # players
        self.players = [Player(p['ID'], p['resources']) for p in map_data.rts_PhysicalGameState.players.rts_Player]

        # terrain
        self.height = int(map_data.rts_PhysicalGameState['height'])
        self.width = int(map_data.rts_PhysicalGameState['width'])
        terrain_str = map_data.rts_PhysicalGameState.terrain.cdata
        assert self.height * self.width == len(terrain_str), \
            'Invalid map dimensions: height * width should equal terrain'
        self.terrain = np.zeros((self.height, self.width), dtype=np.uint8)
        i = 0
        for y in range(self.height):
            for x in range(self.width):
                self.terrain[y, x] = terrain_str[i]
                i += 1

        # units
        self.units = {}
        self.unit_map = np.zeros((self.height, self.width), dtype=np.uint8)
        for unit in map_data.rts_PhysicalGameState.units.rts_units_Unit:
            unit_id = int(unit['ID'])
            unit_cls = unit_classes[unit['type']]
            pos = Position(int(unit['x']), int(unit['y']))
            self.units[unit_id] = unit_cls(unit_id, unit['player'], pos)
            self.unit_map[pos.y, pos.x] = UnitEncoding[unit_cls.__name__].value

    def get_state(self, unit_id) -> np.ndarray:
        assert unit_id in self.units
        state = self.terrain.copy() + self.unit_map.copy()
        unit = self.units[unit_id]
        state[unit.y, unit.x] += len(UnitEncoding)
        return state

    def _read_map_file(self, map_filename):
        return untangle.parse(os.path.join('pycrorts3', 'envs', 'game', 'maps', map_filename))
