"""Генерация уровня: комнаты, коридоры, старт, выход и наполнение."""
from __future__ import annotations

import random

from domain.balance import (
    ENEMIES_START,
    ENEMIES_STEP,
    EXTRA_CORRIDORS,
    GRID_COLS,
    GRID_ROWS,
    LEVEL_H,
    LEVEL_W,
    LEVELS,
    ROOM_MAX_H,
    ROOM_MAX_W,
    ROOM_MIN_H,
    ROOM_MIN_W,
    SECTION_H,
    SECTION_W,
    USEFUL_END,
    USEFUL_START,
)
from domain.entities import create_enemy, pick_enemy_kind
from domain.geometry import bfs_distances
from domain.items import (
    GUARANTEED_TYPES,
    random_template,
    random_template_of_type,
    roll_item,
)
from domain.level import WALKABLE, Corridor, Level, Pos, Room, Tile
from domain.validation import find_problems, lock_count, place_locks


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
    """Обход со стеком строит остовное дерево, затем добавляем несколько лишних рёбер."""
    edges = grid_edges()
    rng.shuffle(edges)
    seen = {0}
    stack = [0]
    chosen = []
    while stack:
        room = stack.pop()
        for a, b in edges:
            if room not in (a, b):
                continue
            neighbor = b if room == a else a
            if neighbor not in seen:
                seen.add(neighbor)
                chosen.append((a, b))
                stack.append(neighbor)
    rest = [edge for edge in edges if edge not in chosen]
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


def enemy_count(level_number: int) -> int:
    return ENEMIES_START + ENEMIES_STEP * (level_number - 1)


def useful_count(level_number: int, total: int = LEVELS) -> int:
    """Полезных предметов на уровне: плавно убывает от USEFUL_START до USEFUL_END."""
    if total <= 1:
        return USEFUL_START
    t = (level_number - 1) / (total - 1)
    return max(len(GUARANTEED_TYPES), round(USEFUL_START + (USEFUL_END - USEFUL_START) * t))


def populate(level: Level, rng: random.Random, total: int = LEVELS) -> None:
    """Кладёт врагов и предметы во все комнаты, кроме стартовой, и не на выход."""
    free = [
        cell
        for room in level.rooms
        if room.id != level.start_room
        for cell in room.cells()
        if cell != level.exit
    ]
    rng.shuffle(free)

    for _ in range(min(enemy_count(level.number), len(free))):
        pos = free.pop()
        level.enemies.append(create_enemy(pick_enemy_kind(level.number, rng), pos, level.number))

    templates = [random_template_of_type(t, rng) for t in GUARANTEED_TYPES]
    while len(templates) < useful_count(level.number, total):
        templates.append(random_template(rng))
    for template in templates[: len(free)]:
        level.items[free.pop()] = roll_item(template, rng)


MAX_ATTEMPTS = 50


def _distances_on(tiles: list[list[Tile]], start: Pos) -> dict[Pos, int]:
    """Расстояния от старта по нарисованной карте, до расстановки дверей."""
    def walkable(pos: Pos) -> bool:
        return (0 <= pos.x < LEVEL_W and 0 <= pos.y < LEVEL_H
                and tiles[pos.y][pos.x] in WALKABLE)

    return bfs_distances(start, walkable)


def generate_level(number: int, rng: random.Random, total: int = LEVELS) -> Level:
    """Генерирует корректный уровень. Некорректные раскладки молча отбрасываются."""
    for _ in range(MAX_ATTEMPTS):
        rooms = build_rooms(rng)
        corridors = [build_corridor(rng, rooms[a], rooms[b]) for a, b in choose_connections(rng)]
        try:
            tiles = paint(rooms, corridors)
        except ValueError:
            continue

        start_room = rng.choice(rooms)
        start = rng.choice(start_room.cells())
        dist = _distances_on(tiles, start)
        if any(room.center not in dist for room in rooms):
            continue

        # выход - в самой далёкой (по пути) комнате
        exit_room = max((r for r in rooms if r is not start_room), key=lambda r: dist[r.center])
        exit_pos = exit_room.center
        tiles[exit_pos.y][exit_pos.x] = Tile.EXIT

        level = Level(
            number=number, width=LEVEL_W, height=LEVEL_H, tiles=tiles,
            rooms=rooms, corridors=corridors, start=start, exit=exit_pos,
            start_room=start_room.id, exit_room=exit_room.id,
        )
        populate(level, rng, total)
        place_locks(level, rng, lock_count(number))
        if not find_problems(level):
            return level
    raise RuntimeError(f"не удалось сгенерировать уровень {number} за {MAX_ATTEMPTS} попыток")
