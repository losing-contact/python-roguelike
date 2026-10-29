from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.entities import Enemy
from domain.models.items import Item
from domain.models.keys import KeyColor
from domain.models.position import Pos
from domain.models.tile import WALKABLE, Tile


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
