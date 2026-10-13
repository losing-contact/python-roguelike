"""Расстановка врагов и предметов по уровню. Чем глубже, тем врагов больше, а помощи меньше."""
from __future__ import annotations

import random

from domain.balance import ENEMIES_START, ENEMIES_STEP, LEVELS, USEFUL_END, USEFUL_START
from domain.catalog import (
    GUARANTEED_TYPES,
    random_template,
    random_template_of_type,
    roll_item,
)
from domain.enemies.factory import create_enemy, pick_enemy_kind
from domain.models.level import Level


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
