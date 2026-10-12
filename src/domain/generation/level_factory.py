"""Сборка уровня целиком: раскладка -> старт и выход -> наполнение -> проверка."""
from __future__ import annotations

import random
from collections.abc import Callable

from domain.balance import LEVEL_H, LEVEL_W, LEVELS
from domain.generation.layout import build_corridor, build_rooms, choose_connections, paint
from domain.generation.populate import populate
from domain.generation.validate import find_problems
from domain.geometry import bfs_distances
from domain.models.level import Level
from domain.models.position import Pos
from domain.models.tile import WALKABLE, Tile

MAX_ATTEMPTS = 50


def _walkable_on(tiles: list[list[Tile]]) -> Callable[[Pos], bool]:
    def walkable(p: Pos) -> bool:
        return 0 <= p.x < LEVEL_W and 0 <= p.y < LEVEL_H and tiles[p.y][p.x] in WALKABLE

    return walkable


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
        dist = bfs_distances(start, _walkable_on(tiles))
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
        if not find_problems(level):
            return level
    raise RuntimeError(f"не удалось сгенерировать уровень {number} за {MAX_ATTEMPTS} попыток")
