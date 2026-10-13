"""Раскладка уровня: 9 комнат (по одной в каждой секции сетки 3x3) и коридоры между ними.

Коридоры - это не просто «вырезанные» клетки: каждый хранит свои проёмы и список клеток,
чтобы по ним можно было ходить, рисовать туман войны и сохранять уровень.
"""
from __future__ import annotations

import random

from domain.balance import (
    EXTRA_CORRIDORS,
    GRID_COLS,
    GRID_ROWS,
    LEVEL_H,
    LEVEL_W,
    ROOM_MAX_H,
    ROOM_MAX_W,
    ROOM_MIN_H,
    ROOM_MIN_W,
)
from domain.models.level import Corridor, Room
from domain.models.position import Pos
from domain.models.tile import Tile

SECTION_W = LEVEL_W // GRID_COLS
SECTION_H = LEVEL_H // GRID_ROWS


def build_rooms(rng: random.Random) -> list[Room]:
    """По одной комнате случайного размера и положения в каждой секции.

    Вокруг пола остаётся место под стену, а у правого и нижнего края секции - свободная
    клетка, поэтому между стенами соседних комнат всегда есть место для коридора.
    """
    rooms = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            sx, sy = col * SECTION_W, row * SECTION_H
            w = rng.randint(ROOM_MIN_W, min(ROOM_MAX_W, SECTION_W - 3))
            h = rng.randint(ROOM_MIN_H, min(ROOM_MAX_H, SECTION_H - 3))
            x = rng.randint(sx + 1, sx + SECTION_W - 2 - w)
            y = rng.randint(sy + 1, sy + SECTION_H - 2 - h)
            rooms.append(Room(id=row * GRID_COLS + col, x=x, y=y, w=w, h=h, row=row, col=col))
    return rooms


def grid_edges() -> list[tuple[int, int]]:
    """Все пары соседних секций (по горизонтали и вертикали), меньший id первым."""
    edges = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            rid = row * GRID_COLS + col
            if col + 1 < GRID_COLS:
                edges.append((rid, rid + 1))
            if row + 1 < GRID_ROWS:
                edges.append((rid, rid + GRID_COLS))
    return edges


def choose_connections(rng: random.Random) -> list[tuple[int, int]]:
    """Случайное остовное дерево (гарантирует связность) плюс несколько лишних рёбер."""
    edges = grid_edges()
    rng.shuffle(edges)
    parent = list(range(GRID_ROWS * GRID_COLS))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    chosen, rest = [], []
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            chosen.append((a, b))
        else:
            rest.append((a, b))
    extra = min(len(rest), rng.randint(*EXTRA_CORRIDORS))
    return chosen + rest[:extra]


def _path(waypoints: list[Pos]) -> list[Pos]:
    """Клетки ломаной по опорным точкам (только горизонтальные/вертикальные отрезки)."""
    cells: list[Pos] = []
    for a, b in zip(waypoints, waypoints[1:]):
        dx = (b.x > a.x) - (b.x < a.x)
        dy = (b.y > a.y) - (b.y < a.y)
        cur = a
        while True:
            if not cells or cells[-1] != cur:
                cells.append(cur)
            if cur == b:
                break
            cur = cur.shifted(dx, dy)
    return cells


def build_corridor(rng: random.Random, a: Room, b: Room) -> Corridor:
    """Коридор между соседними секциями: от стены комнаты a до стены комнаты b."""
    if a.row == b.row:  # b правее a
        ya = rng.randint(a.y, a.y + a.h - 1)
        yb = rng.randint(b.y, b.y + b.h - 1)
        door_a, door_b = Pos(a.x + a.w, ya), Pos(b.x - 1, yb)
        xs, xe = door_a.x + 1, door_b.x - 1
        xm = rng.randint(xs, xe)
        way = [Pos(xs, ya), Pos(xm, ya), Pos(xm, yb), Pos(xe, yb)]
    else:               # b ниже a
        xa = rng.randint(a.x, a.x + a.w - 1)
        xb = rng.randint(b.x, b.x + b.w - 1)
        door_a, door_b = Pos(xa, a.y + a.h), Pos(xb, b.y - 1)
        ys, ye = door_a.y + 1, door_b.y - 1
        ym = rng.randint(ys, ye)
        way = [Pos(xa, ys), Pos(xa, ym), Pos(xb, ym), Pos(xb, ye)]
    return Corridor(a.id, b.id, door_a, door_b, _path(way))


def paint(rooms: list[Room], corridors: list[Corridor]) -> list[list[Tile]]:
    """Рисует на сетке стены, пол, коридоры и проёмы. ValueError - если геометрия сломана."""
    tiles = [[Tile.VOID] * LEVEL_W for _ in range(LEVEL_H)]
    for room in rooms:
        for yy in range(room.y - 1, room.y + room.h + 1):
            for xx in range(room.x - 1, room.x + room.w + 1):
                inside = room.contains(Pos(xx, yy))
                tiles[yy][xx] = Tile.FLOOR if inside else Tile.WALL
    for corridor in corridors:
        for cell in corridor.cells:
            if tiles[cell.y][cell.x] not in (Tile.VOID, Tile.CORRIDOR):
                raise ValueError(f"коридор пересёк комнату в {cell}")
            tiles[cell.y][cell.x] = Tile.CORRIDOR
        for door in (corridor.door_a, corridor.door_b):
            if tiles[door.y][door.x] is not Tile.WALL:
                raise ValueError(f"проём {door} не в стене")
            tiles[door.y][door.x] = Tile.DOORWAY
    return tiles
