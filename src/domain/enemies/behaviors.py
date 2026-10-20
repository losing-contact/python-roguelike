"""Паттерны передвижения врагов, когда игрока рядом нет.

Каждый тип врага может иметь свой паттерн. Новый тип добавляется функцией
и записью в PATTERNS; остальной код не меняется (стратегия).
"""
from __future__ import annotations

import random
from collections.abc import Callable

from domain.enemies.types import EnemyKind
from domain.models.entities import Enemy
from domain.models.level import Level
from domain.models.position import Pos
from domain.models.tile import Tile

Pattern = Callable[[Enemy, Level, random.Random], Pos | None]


def random_walk(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Случайный шаг по комнате (в коридоре - по любой проходимой клетке)."""
    in_room = level.tile_at(enemy.pos) is Tile.FLOOR
    options = [
        p for p in enemy.pos.neighbors()
        if level.can_enemy_enter(p) and (not in_room or level.tile_at(p) is Tile.FLOOR)
    ]
    return rng.choice(options) if options else None


def room_cells(level: Level, start: Pos) -> list[Pos]:
    """Клетки пола комнаты, где стоит start (заливка по Tile.FLOOR)."""
    seen = {start}
    stack = [start]
    while stack:
        cell = stack.pop()
        for neighbor in cell.neighbors():
            if neighbor not in seen and level.tile_at(neighbor) is Tile.FLOOR:
                seen.add(neighbor)
                stack.append(neighbor)
    return list(seen)


def teleport(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Прыжок на случайную свободную клетку той же комнаты (привидение)."""
    if level.tile_at(enemy.pos) is not Tile.FLOOR:
        return random_walk(enemy, level, rng)      # в коридоре - обычный шаг
    options = [
        p for p in room_cells(level, enemy.pos)
        if p != enemy.pos and level.can_enemy_enter(p)
    ]
    return rng.choice(options) if options else None


def two_step_walk(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Шаг на две клетки: сначала соседняя клетка, потом ещё одна от неё (огр)."""
    in_room = level.tile_at(enemy.pos) is Tile.FLOOR

    def ok(p: Pos) -> bool:
        return level.can_enemy_enter(p) and (not in_room or level.tile_at(p) is Tile.FLOOR)

    options = [
        second
        for first in enemy.pos.neighbors() if ok(first)
        for second in first.neighbors() if second != enemy.pos and ok(second)
    ]
    return rng.choice(options) if options else random_walk(enemy, level, rng)


PATTERNS: dict[EnemyKind, Pattern] = {
    EnemyKind.ZOMBIE: random_walk,
    EnemyKind.VAMPIRE: random_walk,
    EnemyKind.GHOST: teleport,
    EnemyKind.OGRE: two_step_walk,
}
