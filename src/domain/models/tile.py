from enum import Enum


class Tile(Enum):
    VOID = "void"          # сплошная порода, не рисуется
    WALL = "wall"          # стена комнаты
    FLOOR = "floor"        # пол комнаты
    DOORWAY = "doorway"    # проём в стене
    CORRIDOR = "corridor"  # коридор между комнатами
    EXIT = "exit"          # блок перехода на следующий уровень


WALKABLE = frozenset({Tile.FLOOR, Tile.DOORWAY, Tile.CORRIDOR, Tile.EXIT})
