"""Описание типов противников (данные, без логики)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.balance import SCALE


class EnemyKind(Enum):
    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    GHOST = "ghost"
    OGRE = "ogre"
    WIZZARD = "wizzard"
    
    # TODO (Задание 2): GHOST, OGRE, SNAKE_MAGE; (Задание 8): MIMIC


class Trait(Enum):
    """Особенности, которые учитывает бой."""

    FIRST_HIT_MISS = "first_hit_miss"      # первый удар по такому врагу - всегда промах
    DRAIN_MAX_HEALTH = "drain_max_health"  # успешная атака отнимает максимальное здоровье
    INVISIBLE_PHASES = "invisible_phases"  # периодически невидим, пока игрок не вступил в бой
    REST_AFTER_ATTACK = "rest_after_attack"  # после атаки отдыхает ход, следующий удар гарантированно попадает
    SLEEP_ON_HIT = "sleep_on_hit"  # успешная атака может усыпить игрока на один ход
    DIAGONAL_MOVE = "diagonal_move"  # в комнате с игроком ходит и бьёт по диагонали


@dataclass(frozen=True)
class EnemySpec:
    kind: EnemyKind
    name: str
    max_health: int
    agility: int
    strength: int
    hostility: int             # с какого расстояния (по пути) начинается преследование
    move_every: int = 1        # враг действует раз в N ходов игрока
    traits: frozenset[Trait] = frozenset()
    step_size: int = 1         # сколько клеток проходит за один ход

SPECS: dict[EnemyKind, EnemySpec] = {
    EnemyKind.ZOMBIE: EnemySpec(
        EnemyKind.ZOMBIE, "Зомби",
        max_health=5 * SCALE, agility=2, strength=1 * SCALE,
        hostility=6, move_every=2,
    ),
    EnemyKind.VAMPIRE: EnemySpec(
        EnemyKind.VAMPIRE, "Вампир",
        max_health=8 * SCALE, agility=4, strength=2 * SCALE,
        hostility=8, move_every=2,
        traits=frozenset({Trait.FIRST_HIT_MISS, Trait.DRAIN_MAX_HEALTH}),
    ),
    EnemyKind.GHOST: EnemySpec(
        EnemyKind.GHOST, "Привидение",
        max_health=2 * SCALE, agility=8, strength=SCALE // 2,
        hostility=3, move_every=2,
        traits=frozenset({Trait.INVISIBLE_PHASES}),
    ),
        EnemyKind.OGRE: EnemySpec(
        EnemyKind.OGRE, "Огр",
        max_health=10 * SCALE, agility=2, strength=3 * SCALE,
        hostility=5, move_every=3, step_size=2,
        traits=frozenset({Trait.REST_AFTER_ATTACK}),
    ),
        EnemyKind.WIZZARD: EnemySpec(
        EnemyKind.WIZZARD, "Маг",
        max_health=5 * SCALE, agility=3, strength=1 * SCALE,
        hostility=6, move_every=2,
        traits=frozenset({Trait.SLEEP_ON_HIT, Trait.DIAGONAL_MOVE}),
    ),
}
