"""Описание типов противников (данные, без логики)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.balance import SCALE


class EnemyKind(Enum):
    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    # TODO (Задание 2): GHOST, OGRE, SNAKE_MAGE; (Задание 8): MIMIC


class Trait(Enum):
    """Особенности, которые учитывает бой."""

    FIRST_HIT_MISS = "first_hit_miss"      # первый удар по такому врагу - всегда промах
    DRAIN_MAX_HEALTH = "drain_max_health"  # успешная атака отнимает максимальное здоровье


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
}
