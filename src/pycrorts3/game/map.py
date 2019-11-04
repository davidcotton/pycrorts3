import os
from typing import Optional

import numpy as np
import pkg_resources
import untangle

from .actions import ActionEncodings, Action, NoopAction, MoveAction, AttackAction, action_encoding_classes
from .player import Player
from .position import Position, cardinal_to_euclidean
from .units import Unit, unit_classes, UnitEncoding


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

    def get_unit(self, unit_id):
        return self.units[unit_id]

    def move_unit(self, unit_id, new_position):
        assert unit_id in self.units
        unit = self.units[unit_id]
        old_x, old_y = unit.position
        new_x, new_y = new_position
        assert self.terrain[new_y, new_x] == 0 and self.unit_map[new_y, new_x] == 0
        self.unit_map[new_y, new_x], self.unit_map[old_y, old_x] = self.unit_map[old_y, old_x], 0
        unit.position = new_position

    def attack_unit(self, unit_id: int, attack_position: Position) -> Optional[Unit]:
        """Execute an attack action.
        If the target moves or dies before the action executes, the attack does not occur.

        :param unit_id: The ID of the attacking unit.
        :param attack_position: The cell to attack.
        :return: An optional target unit if dead, else None.
        """
        attacker = self.units[unit_id]
        for target in self.units.values():
            if target.position == attack_position:
                break
        else:
            # target may have move or died before attack action executed
            return None
        target.hitpoints -= attacker.deal_damage()
        if target.hitpoints <= 0:
            # pass the dead unit back to the main class so it can clear up any references to it
            return target

    def remove_unit(self, unit_id: int) -> None:
        """Remove a unit from the game (after it has died).

        :param unit_id: The ID of the unit to remove.
        """
        unit = self.units.pop(unit_id)
        self.unit_map[unit.y, unit.x] = 0

    def is_legal_action(self, action: Action) -> bool:
        """Check an action is consistent with game rules/state?

        :param action: The action to check legality of.
        :return: True if the action is legal, else False.
        """
        if isinstance(action, NoopAction):
            return True  # just assume all NOOPs are valid for now
        x, y = action.position
        if not(0 <= x < self.width and 0 <= y < self.height):
            is_valid = False  # must be within map bounds
        elif isinstance(action, MoveAction):  # ensure cell isn't occupied
            is_valid = self.terrain[y, x] == 0 and self.unit_map[y, x] == 0
        elif isinstance(action, AttackAction):  # ensure target cell IS occupied by an ENEMY unit
            attacker = self.units[action.unit_id]
            is_valid = False
            for unit in self.units.values():
                if unit.position == action.position:  # can't attack empty cell
                    is_valid = attacker.player_id != unit.player_id  # only attack enemy
                    break
        else:
            raise ValueError('Invalid action')
        return is_valid

    def get_action_mask(self, unit: Unit) -> np.array:
        """Generate a bit mask for all actions.

        :param unit: The unit to generate the mask for.
        :return: A numpy array where 0=invalid & 1=valid.
        """
        mask = [1] * len(ActionEncodings)
        for action_type in ActionEncodings:
            if action_type.name == 'NOOP':
                continue  # assume always valid
            action_cls = action_encoding_classes[action_type]
            new_posn = cardinal_to_euclidean(unit.position, action_type.name)
            action = action_cls(unit.id, new_posn, 0, 0)
            mask[action_type.value] = int(self.is_legal_action(action))
        return np.array(mask, dtype=np.uint8)

    def to_array(self, unit_id=None) -> np.ndarray:
        """Export a 2D representation of the game state.

        :param unit_id: Optionally present the state from the view of a unit.
        :return: A 2D numpy array.
        """
        state = self.terrain.copy() + self.unit_map.copy()
        if unit_id is not None:
            assert unit_id in self.units
            unit = self.units[unit_id]
            state[unit.y, unit.x] += len(UnitEncoding)
        return state

    def _read_map_file(self, map_filename: str):
        """Read a XML microRTS map file.

        :param map_filename: The name of the file, e.g. `4x4_melee_light2.xml`
        :return: The map data.
        """
        map_data = pkg_resources.resource_string(__name__, os.path.join('maps', map_filename)).decode('utf-8')
        return untangle.parse(map_data)
