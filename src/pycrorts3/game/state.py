from copy import deepcopy
import os
from typing import Dict, Optional, Type

import numpy as np
import pkg_resources
import untangle

from .actions import ActionEncodings, action_encoding_classes, Action, NoopAction, MoveAction, AttackAction, \
    HarvestAction, ReturnAction, ProduceAction
from .player import Player
from .position import Position, cardinal_to_euclidean
from .units import Unit, UnitEncoding, Resource, BaseBuilding, BarracksBuilding, WorkerUnit, LightUnit

HARVEST_AMOUNT = 1


class State:
    def __init__(self, map_filename: str) -> None:
        super().__init__()
        map_data = self._read_map_file(map_filename)

        # players
        self.players = [Player.from_xml(p) for p in map_data.rts_PhysicalGameState.players.rts_Player]

        # terrain
        self.height = int(map_data.rts_PhysicalGameState['height'])
        self.width = int(map_data.rts_PhysicalGameState['width'])
        terrain_str = map_data.rts_PhysicalGameState.terrain.cdata
        assert self.height * self.width == len(terrain_str), 'Invalid map dimensions: height * width != len(terrain)'
        self.terrain = np.zeros((self.height, self.width), dtype=np.uint8)
        i = 0
        for y in range(self.height):
            for x in range(self.width):
                self.terrain[y, x] = terrain_str[i]
                i += 1

        # units
        self.units: Dict[int, Unit] = {}
        self.unit_map = np.zeros((self.height, self.width), dtype=np.uint8)
        for unit_xml in map_data.rts_PhysicalGameState.units.rts_units_Unit:
            unit = Unit.from_xml(unit_xml)
            self.units[unit.id] = unit
            self.unit_map[unit.y, unit.x] = UnitEncoding[unit.__class__.__name__].value

        self.initial_values = {
            'players': deepcopy(self.players),
            'terrain': deepcopy(self.terrain),
            'units': deepcopy(self.units),
            'unit_map': deepcopy(self.unit_map),
        }

    def reset(self) -> None:
        self.players = deepcopy(self.initial_values['players'])
        self.terrain = deepcopy(self.initial_values['terrain'])
        self.units = deepcopy(self.initial_values['units'])
        self.unit_map = deepcopy(self.initial_values['unit_map'])

    def move_unit(self, unit_id: int, new_position: Position) -> None:
        """Move a unit to a new position.

        :param unit_id: The ID of the unit to move.
        :param new_position: The new position to move to.
        """
        unit = self.units[unit_id]
        assert not unit.is_dead()
        old_x, old_y = unit.position
        new_x, new_y = new_position
        assert self.terrain[new_y, new_x] == 0 and self.unit_map[new_y, new_x] == 0
        self.unit_map[new_y, new_x], self.unit_map[old_y, old_x] = self.unit_map[old_y, old_x], 0
        unit.position = new_position

    def attack_unit(self, unit_id: int, attack_position: Position) -> Optional[Unit]:
        """Execute an attack action.

        If the target moves or dies before the action executes, the attack does not occur.
        If the target unit was killed, pass it back to the Game class so it can clear up any references to it
          before removing.

        :param unit_id: The ID of the attacking unit.
        :param attack_position: The cell to attack.
        :return: An optional target unit if dead, else None.
        """
        attacker = self.units[unit_id]
        assert not attacker.is_dead()
        for target in self.units.values():
            if target.position == attack_position:
                break
        else:
            return None  # target may have move or died before attack action executed
        assert not isinstance(target, Resource)
        target.hitpoints -= attacker.deal_damage()
        if target.hitpoints <= 0:
            return target

    def remove_unit(self, unit: Unit) -> None:
        """Remove a unit from the game (e.g. after it has died or been mined out).

        We leave dead units in `self.units` to get around RLlib.MultiAgent not liking agents obs disappearing.
        However we set their location to None so other units can occupy their former location

        :param unit: The unit to remove.
        """
        self.unit_map[unit.y, unit.x] = 0
        unit.position = None

    def harvest(self, unit_id: int, harvest_position: Position) -> None:
        """A worker unit harvests minerals from an adjacent mineral patch.

        :param unit_id: The ID of the worker unit harvesting.
        :param harvest_position: The position to harvest.
        """
        harvester = self.units[unit_id]
        assert not harvester.is_dead()
        for unit in self.units.values():
            if isinstance(unit, Resource) and unit.position == harvest_position:
                minerals = unit
                break
        else:
            return

        harvest_amount = HARVEST_AMOUNT if minerals.resources > HARVEST_AMOUNT else minerals.resources
        assert harvest_amount > 0
        harvester.resources += harvest_amount
        minerals.resources -= harvest_amount
        assert minerals.resources >= 0
        if minerals.resources == 0:
            self.remove_unit(minerals)

    def return_minerals(self, unit_id: int, base_position: Position) -> None:
        """A worker unit can return harvested minerals to an adjacent BaseBuilding.

        :param unit_id: The ID of the worker unit returning harvested minerals.
        :param base_position: The position of the BaseBuilding receiving the minerals.
        """
        harvester = self.units[unit_id]
        assert not harvester.is_dead()
        assert harvester.resources
        for base in self.units.values():
            if isinstance(base, BaseBuilding) \
                    and base.player_id == harvester.player_id \
                    and base.position == base_position:
                break
        else:
            return
        assert self._manhattan_distance(harvester.position, base.position) == 1
        player = self.players[harvester.player_id]
        player.minerals += harvester.resources
        harvester.resources = 0

    def produce(self, unit_id: int, produce_position: Position, produce_type: Type[Unit]) -> None:
        producer = self.units[unit_id]
        assert not producer.is_dead()
        player = self.players[producer.player_id]
        x, y = produce_position
        if self.terrain[y, x] != 0 or self.unit_map[y, x] != 0:
            return
        if player.minerals < produce_type.cost:
            return
        player.minerals -= produce_type.cost
        unit_ids = sorted(self.units.keys())
        new_unit_id = unit_ids[-1] + 1
        new_unit = produce_type(new_unit_id, producer.player_id, produce_position)
        self.units[new_unit.id] = new_unit

    def is_legal_action(self, action: Action) -> bool:
        """Check an action is consistent with game rules/state?

        :param action: The action to check legality of.
        :return: True if the action is legal, else False.
        """
        if isinstance(action, NoopAction):
            return True  # nothing to check
        x, y = action.position
        if not(0 <= x < self.width and 0 <= y < self.height):
            return False  # must be within map bounds
        elif isinstance(action, MoveAction):  # ensure cell isn't occupied
            unit = self.units[action.unit_id]
            if isinstance(unit, (Resource, BaseBuilding, BarracksBuilding)):
                return False
            if self._manhattan_distance(unit.position, action.position) != 1:
                return False  # must be adjacent
            return self.terrain[y, x] == 0 and self.unit_map[y, x] == 0
        elif isinstance(action, AttackAction):  # ensure target cell IS occupied by an ENEMY unit
            attacker = self.units[action.unit_id]
            if isinstance(attacker, (Resource, BaseBuilding, BarracksBuilding)):
                return False
            if self._manhattan_distance(attacker.position, action.position) > attacker.attack_range:
                return False  # must be within attack range
            for target in self.units.values():
                if target.position == action.position:  # can't attack empty cell
                    return attacker.player_id == (1 - target.player_id)  # only attack enemy
            else:
                return False
        elif isinstance(action, HarvestAction):
            harvester = self.units[action.unit_id]
            if not isinstance(harvester, WorkerUnit):
                return False  # only workers can harvest minerals
            if harvester.resources:
                return False  # workers can only carry one load at one time
            # if self._manhattan_distance(harvester.position, action.position) != 1:
            #     return False  # worker must be adjacent to minerals to mine
            for minerals in self.units.values():
                if isinstance(minerals, Resource) and minerals.position == action.position:
                    return True
            else:
                return False
        elif isinstance(action, ReturnAction):
            harvester = self.units[action.unit_id]
            if not isinstance(harvester, WorkerUnit):
                return False  # only workers can harvest/return minerals
            if harvester.resources <= 0:
                return False  # worker must have minerals to return
            for base in self.units.values():
                if isinstance(base, BaseBuilding) \
                        and base.position == action.position\
                        and base.player_id == harvester.player_id:
                    break
            else:
                return False  # action position must be a base on the harvester's team
            # if self._manhattan_distance(harvester.position, action.position) != 1:
            #     return False  # worker must be adjacent to base to return
            return True
        elif isinstance(action, ProduceAction):
            producer = self.units[action.unit_id]
            if not producer.produces:
                return False  # has nothing to produce
            player = self.players[producer.player_id]
            producing = action.produce_type
            if producing.cost > player.minerals:
                return False  # can't afford
            if self.terrain[y, x] != 0 or self.unit_map[y, x] != 0:
                return False  # new unit location must be vacant
            # if self._manhattan_distance(producer.position, action.position) != 1:
            #     return False  # new unit must be adjacent to producer
            return True
        else:
            raise ValueError('Invalid action')

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
            if action_cls == ProduceAction:
                # action = action_cls(unit.id, new_posn, 0, 0, LightUnit)
                action = action_cls(unit.id, new_posn, 0, 0, WorkerUnit)
            else:
                action = action_cls(unit.id, new_posn, 0, 0)
            mask[action_type.value] = int(self.is_legal_action(action))
        return np.array(mask, dtype=np.uint8)

    def get_unit(self, unit_id: int) -> Unit:
        return self.units[unit_id]

    def to_array(self, unit_id=None) -> np.ndarray:
        """Export a 2D representation of the game state.

        :param unit_id: Optionally present the state from the view of a unit.
        :return: A 2D numpy array.
        """
        state = self.terrain.copy() + self.unit_map.copy()
        if unit_id is not None:
            unit = self.units[unit_id]
            if not unit.is_dead():
                state[unit.y, unit.x] += len(UnitEncoding)
            for other in self.units.values():
                if other.is_dead():
                    continue
                elif other.player_id == unit.player_id:
                    state[other.y, other.x] += len(UnitEncoding)
        return state

    def _read_map_file(self, map_filename: str):
        """Read a XML microRTS map file.

        :param map_filename: The name of the file, e.g. `4x4_melee_light2`
        :return: The map data.
        """
        map_data = pkg_resources.resource_string(__name__, os.path.join('maps', map_filename + '.xml')).decode('utf-8')
        return untangle.parse(map_data)

    @staticmethod
    def _manhattan_distance(start: Position, goal: Position) -> int:
        return abs(goal.x - start.x) + abs(goal.y - start.y)
