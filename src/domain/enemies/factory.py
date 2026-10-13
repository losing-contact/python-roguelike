from __future__ import annotations

import random

from domain.balance import (
    ENEMY_GROWTH,
    VAMPIRE_CHANCE_MAX,
    VAMPIRE_CHANCE_START,
    VAMPIRE_CHANCE_STEP,
)
from domain.enemies.types import SPECS, EnemyKind
from domain.models.entities import Enemy
from domain.models.position import Pos


def create_enemy(kind: EnemyKind, pos: Pos, level: int) -> Enemy:
    """Создаёт врага; с глубиной уровня здоровье и сила растут, ловкость - медленно."""
    spec = SPECS[kind]
    k = ENEMY_GROWTH ** (level - 1)
    max_health = round(spec.max_health * k)
    return Enemy(
        spec=spec,
        pos=pos,
        health=max_health,
        max_health=max_health,
        agility=spec.agility + (level - 1) // 3,
        strength=round(spec.strength * k),
    )


def pick_enemy_kind(level: int, rng: random.Random) -> EnemyKind:
    """Чем глубже уровень, тем чаще встречаются сильные враги."""
    vampire_chance = min(
        VAMPIRE_CHANCE_MAX, VAMPIRE_CHANCE_START + VAMPIRE_CHANCE_STEP * (level - 1)
    )
    return EnemyKind.VAMPIRE if rng.random() < vampire_chance else EnemyKind.ZOMBIE
