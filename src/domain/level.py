"""Карта: координаты, типы клеток, комнаты, коридоры, ключи и память исследования."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from domain.items import Item

if TYPE_CHECKING:
    from domain.entities import Enemy

CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class Pos:
    """Клетка карты: x - столбец, y - строка."""

    x: int
    y: int

    def shifted(self, dx: int, dy: int) -> Pos:
        return Pos(self.x + dx, self.y + dy)

    def manhattan(self, other: Pos) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def neighbors(self) -> list[Pos]:
        return [self.shifted(dx, dy) for dx, dy in CARDINALS]


class Tile(Enum):
    VOID = "void"          # сплошная порода, не рисуется
    WALL = "wall"          # стена комнаты
    FLOOR = "floor"        # пол комнаты
    DOORWAY = "doorway"    # проём в стене
    CORRIDOR = "corridor"  # коридор между комнатами
    EXIT = "exit"          # блок перехода на следующий уровень


WALKABLE = frozenset({Tile.FLOOR, Tile.DOORWAY, Tile.CORRIDOR, Tile.EXIT})


class KeyColor(Enum):
    RED = "red"
    YELLOW = "yellow"
    BLUE = "blue"


@dataclass
class Room:
    """Комната: id, положение пола (x, y, w, h) и секция сетки 3x3."""

    id: int
    x: int
    y: int
    w: int
    h: int
    row: int
    col: int

    def contains(self, pos: Pos) -> bool:
        return self.x <= pos.x < self.x + self.w and self.y <= pos.y < self.y + self.h

    def cells(self) -> list[Pos]:
        return [Pos(xx, yy) for yy in range(self.y, self.y + self.h)
                for xx in range(self.x, self.x + self.w)]

    def footprint(self) -> list[Pos]:
        """Пол и окружающее кольцо стен (с проёмами и углами): всё, что видно изнутри комнаты."""
        return [Pos(xx, yy) for yy in range(self.y - 1, self.y + self.h + 1)
                for xx in range(self.x - 1, self.x + self.w + 1)]

    @property
    def center(self) -> Pos:
        return Pos(self.x + self.w // 2, self.y + self.h // 2)


@dataclass
class Corridor:
    """Коридор между двумя комнатами: проёмы в стенах и все клетки пути."""

    room_a: int
    room_b: int
    door_a: Pos
    door_b: Pos
    cells: list[Pos] = field(default_factory=list)


@dataclass
class Level:
    number: int
    width: int
    height: int
    tiles: list[list[Tile]]
    rooms: list[Room]
    corridors: list[Corridor]
    start: Pos
    exit: Pos
    start_room: int
    exit_room: int
    enemies: list[Enemy] = field(default_factory=list)
    items: dict[Pos, Item] = field(default_factory=dict)

    doors: dict[Pos, KeyColor] = field(default_factory=dict)
    keys: dict[Pos, KeyColor] = field(default_factory=dict)

    # --- карта ---------------------------------------------------------
    def in_bounds(self, pos: Pos) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def tile_at(self, pos: Pos) -> Tile:
        if not self.in_bounds(pos):
            return Tile.VOID
        return self.tiles[pos.y][pos.x]

    def is_walkable(self, pos: Pos) -> bool:
        return self.tile_at(pos) in WALKABLE and pos not in self.doors

    def room_at(self, pos: Pos) -> Room | None:
        for room in self.rooms:
            if room.contains(pos):
                return room
        return None

    # --- существа ------------------------------------------------------
    def enemy_at(self, pos: Pos) -> Enemy | None:
        for enemy in self.enemies:
            if enemy.pos == pos:
                return enemy
        return None

    def can_enemy_enter(self, pos: Pos) -> bool:
        """Враг может встать на клетку: проходимая, не выход и не занята другим врагом."""
        return (
            self.is_walkable(pos)
            and self.tile_at(pos) is not Tile.EXIT
            and self.enemy_at(pos) is None
        )


@dataclass
class Exploration:
    """Что игрок уже видел на текущем уровне. Это состояние нужно сохранять.

    Хранятся только клетки (позиции). Что именно показывать на месте увиденной клетки,
    решает слой отображения: см. presentation/theme.py::REMEMBERED_TILES.
    """

    seen: set[Pos] = field(default_factory=set)
