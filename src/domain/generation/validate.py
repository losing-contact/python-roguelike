"""Проверка сгенерированного уровня. Пустой список проблем = уровень корректен."""
from __future__ import annotations

from domain.balance import GRID_COLS, GRID_ROWS
from domain.generation.layout import SECTION_H, SECTION_W
from domain.generation.locks import lock_problems
from domain.geometry import bfs_distances
from domain.models.level import Level
from domain.models.tile import WALKABLE, Tile


def reachable_from_start(level: Level) -> dict:
    """Связность карты при открытых дверях; ключи проверяет lock_problems."""
    return bfs_distances(level.start, lambda pos: level.tile_at(pos) in WALKABLE)


def find_problems(level: Level) -> list[str]:
    problems: list[str] = []

    if len(level.rooms) != GRID_ROWS * GRID_COLS:
        problems.append(f"комнат {len(level.rooms)}, ожидалось {GRID_ROWS * GRID_COLS}")

    for room in level.rooms:
        sx, sy = room.col * SECTION_W, room.row * SECTION_H
        if not (sx < room.x and room.x + room.w <= sx + SECTION_W - 1
                and sy < room.y and room.y + room.h <= sy + SECTION_H - 1):
            problems.append(f"комната {room.id} выходит за свою секцию")

    reach = reachable_from_start(level)
    for room in level.rooms:
        if any(cell not in reach for cell in room.cells()):
            problems.append(f"комната {room.id} недостижима из старта")
    if level.exit not in reach:
        problems.append("выход недостижим")

    exits = [(x, y) for y, row in enumerate(level.tiles) for x, t in enumerate(row)
             if t is Tile.EXIT]
    if exits != [(level.exit.x, level.exit.y)]:
        problems.append("на уровне должен быть ровно один блок выхода")
    if level.start_room == level.exit_room:
        problems.append("старт и выход в одной комнате")

    for corridor in level.corridors:
        if any(level.tile_at(c) is not Tile.CORRIDOR for c in corridor.cells):
            problems.append("в коридоре есть клетки не-коридора")
        if any(level.tile_at(d) is not Tile.DOORWAY for d in (corridor.door_a, corridor.door_b)):
            problems.append("проём коридора не отмечен")

    start_room = level.rooms[level.start_room]
    seen = set()
    for enemy in level.enemies:
        if level.tile_at(enemy.pos) is not Tile.FLOOR:
            problems.append(f"враг вне пола комнаты: {enemy.pos}")
        if start_room.contains(enemy.pos):
            problems.append("враг в стартовой комнате")
        if enemy.pos in seen:
            problems.append(f"два врага на клетке {enemy.pos}")
        seen.add(enemy.pos)
    for pos in level.items:
        if start_room.contains(pos):
            problems.append("предмет в стартовой комнате")
        if pos in seen:
            problems.append(f"предмет и враг на клетке {pos}")
        if level.tile_at(pos) is not Tile.FLOOR:
            problems.append(f"предмет вне пола комнаты: {pos}")
    problems += lock_problems(level)
    return problems
