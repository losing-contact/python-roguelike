"""События: что произошло в мире. Домен не знает, как их показать пользователю."""
from __future__ import annotations

from dataclasses import dataclass

from domain.enemies.types import EnemyKind
from domain.models.items import Item


@dataclass(frozen=True)
class Moved:
    pass


@dataclass(frozen=True)
class PlayerAttacked:
    target: EnemyKind
    hit: bool
    damage: int


@dataclass(frozen=True)
class EnemyAttacked:
    attacker: EnemyKind
    hit: bool
    damage: int
    drained_max_health: int = 0
    slept: bool = False


@dataclass(frozen=True)
class PlayerSlept:
    pass


@dataclass(frozen=True)
class EnemyKilled:
    kind: EnemyKind
    treasure: int


@dataclass(frozen=True)
class ItemPickedUp:
    item: Item


@dataclass(frozen=True)
class BackpackFull:
    item: Item


@dataclass(frozen=True)
class ItemUsed:
    item: Item


@dataclass(frozen=True)
class WeaponEquipped:
    item: Item


@dataclass(frozen=True)
class WeaponUnequipped:
    item: Item


@dataclass(frozen=True)
class WeaponDropped:
    item: Item


@dataclass(frozen=True)
class EffectExpired:
    pass


@dataclass(frozen=True)
class LevelChanged:
    level: int


@dataclass(frozen=True)
class PlayerDied:
    pass


@dataclass(frozen=True)
class GameWon:
    pass


Event = (
    Moved | PlayerAttacked | EnemyAttacked | EnemyKilled | ItemPickedUp | BackpackFull
    | ItemUsed | WeaponEquipped | WeaponUnequipped | WeaponDropped | EffectExpired
    | LevelChanged | PlayerDied | GameWon | PlayerSlept
)
