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


PATTERNS: dict[EnemyKind, Pattern] = {
    EnemyKind.ZOMBIE: random_walk,
    EnemyKind.VAMPIRE: random_walk,
}
