import unit

from typing import Tuple
from abc import ABC


class Action(ABC):
    pass


class Attack(Action):
    def __init__(self, attacking: unit.Unit, defending: unit.Unit):
        super().__init__()
        self.attacking: unit.Unit = attacking
        self.defending: unit.Unit = defending

    def __str__(self):
        return f"{self.attacking.name} vs {self.defending.name}"


class Move(Action):
    def __init__(self, who: unit.Unit, where: Tuple[int, int]):
        super().__init__()
        self.who: unit.Unit = who
        self.where: Tuple[int, int] = where

    def __str__(self):
        return f"Move {self.who.name} to {self.where}"
