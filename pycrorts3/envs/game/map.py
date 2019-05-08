from typing import Dict

from pycrorts3.envs.game.position import Position
from pycrorts3.envs.game.units import Unit


class Map:

    def __init__(self) -> None:
        super().__init__()
        self.height = 0
        self.width = 0
        self.terrain = [[]]
        self.units: Dict[Position, Unit] = {}
