from __future__ import annotations

from dataclasses import dataclass, field

from domain.balance import (
    MIN_HEALTH_AFTER_EFFECT,
    MIN_MAX_HEALTH,
    PLAYER_AGILITY,
    PLAYER_MAX_HEALTH,
    PLAYER_STRENGTH,
    SCALE,
)
from domain.enemies.types import EnemyKind, EnemySpec, Trait
from domain.models.items import Backpack, Item, Stat
from domain.models.position import Pos


@dataclass
class ActiveEffect:
    """Временный бонус от эликсира."""

    stat: Stat
    amount: int
    turns_left: int


class Entity:
    """Общее для персонажа и противников: здоровье, ловкость, сила."""

    pos: Pos
    health: int
    max_health: int
    agility: int
    strength: int
    first_hit_spent: bool = False

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def attack_power(self) -> int:
        return self.strength

    @property
    def traits(self) -> frozenset[Trait]:
        return frozenset()

    @property
    def health_blocks(self) -> int:
        """Блоков полоски здоровья; минимум 1, пока жив."""
        return -(-self.health // SCALE)

    @property
    def max_blocks(self) -> int:
        return self.max_health // SCALE


class Character(Entity):
    def __init__(self, pos: Pos | None = None) -> None:
        self.pos = pos or Pos(0, 0)
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.asleep = 0          # ходов, которые игрок пропустит
        self.agility = PLAYER_AGILITY
        self.strength = PLAYER_STRENGTH
        self.weapon: Item | None = None
        self.backpack = Backpack()
        self.effects: list[ActiveEffect] = []

    @property
    def attack_power(self) -> int:
        return self.strength + (self.weapon.strength if self.weapon else 0)

    # --- лечение и характеристики -------------------------------------
    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def apply_permanent(self, stat: Stat, amount: int) -> None:
        self._change(stat, amount)

    def apply_temporary(self, stat: Stat, amount: int, turns: int) -> None:
        self._change(stat, amount)
        self.effects.append(ActiveEffect(stat, amount, turns))

    def tick_effects(self) -> list[ActiveEffect]:
        """Один ход прошёл. Возвращает эффекты, которые только что закончились."""
        expired = []
        for effect in self.effects:
            effect.turns_left -= 1
            if effect.turns_left <= 0:
                expired.append(effect)
        for effect in expired:
            self.effects.remove(effect)
            self._change(effect.stat, -effect.amount)
        return expired

    def _change(self, stat: Stat, amount: int) -> None:
        if stat is Stat.MAX_HEALTH:
            old_max = self.max_health
            self.max_health = max(MIN_MAX_HEALTH, old_max + amount) 
            delta = self.max_health - old_max          # реальное изменение, с учётом зажима
            self.health = min(self.health + delta, self.max_health)
            self.health = max(self.health, MIN_HEALTH_AFTER_EFFECT)
        elif stat is Stat.AGILITY:
            self.agility += amount
        elif stat is Stat.STRENGTH:
            self.strength += amount


@dataclass(eq=False)  # сравнение по тождеству: два зомби с одинаковым здоровьем - разные враги
class Enemy(Entity):
    spec: EnemySpec
    pos: Pos
    health: int
    max_health: int
    agility: int
    strength: int
    timer: int = 0                                  # счётчик ходов для move_every
    first_hit_spent: bool = field(default=False)    # вампир: первый удар уже «промазан»

    @property
    def kind(self) -> EnemyKind:
        return self.spec.kind

    @property
    def hostility(self) -> int:
        return self.spec.hostility

    @property
    def traits(self) -> frozenset[Trait]:
        return self.spec.traits

    invisible: bool = False
    phase_turns: int = 3
    resting: bool = False
    counter_ready: bool = False
    disguised: bool = False 
