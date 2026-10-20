"""Бой: проверка попадания, расчёт и применение урона.

Три этапа удара из задания: попадание -> урон -> применение.
Случайность приходит снаружи (rng), поэтому бой легко проверять тестами.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from domain.balance import (
    HIT_BASE,
    HIT_MAX,
    HIT_MIN,
    HIT_PER_AGILITY,
    MIN_MAX_HEALTH,
    SCALE,
    VAMPIRE_DRAIN,
)
from domain.enemies.types import Trait
from domain.models.entities import Entity


@dataclass(frozen=True)
class AttackResult:
    hit: bool
    damage: int = 0
    drained_max_health: int = 0


def hit_chance(attacker: Entity, target: Entity) -> float:
    chance = HIT_BASE + HIT_PER_AGILITY * (attacker.agility - target.agility)
    return min(HIT_MAX, max(HIT_MIN, chance))


def resolve_attack(attacker: Entity, target: Entity, rng: random.Random) -> AttackResult:

    # особенность огра: после удара отдыхает, а следующий удар гарантированно попадает
    ogre = Trait.REST_AFTER_ATTACK in attacker.traits
    guaranteed = ogre and attacker.counter_ready
    if ogre:
        attacker.counter_ready = False
        attacker.resting = True

    # особенность вампира: первый удар по нему всегда мимо
    if Trait.FIRST_HIT_MISS in target.traits and not target.first_hit_spent:
        target.first_hit_spent = True
        return AttackResult(hit=False)

    # 1. попадание
    if not guaranteed and rng.random() > hit_chance(attacker, target):
        return AttackResult(hit=False)

    # 2. урон
    damage = attacker.attack_power

    # 3. применение
    target.health = max(0, target.health - damage)

    drained = 0
    if Trait.DRAIN_MAX_HEALTH in attacker.traits and target.alive:
        drained = min(VAMPIRE_DRAIN, max(0, target.max_health - MIN_MAX_HEALTH))
        target.max_health -= drained
        target.health = min(target.health, target.max_health)
    return AttackResult(hit=True, damage=damage, drained_max_health=drained)


def treasure_value(enemy: Entity, hostility: int, rng: random.Random) -> int:
    """Сколько сокровищ выпадает: зависит от здоровья, силы, ловкости и враждебности."""
    base = enemy.max_health // SCALE + enemy.strength // SCALE + enemy.agility + hostility
    return rng.randint(max(1, base // 2), max(1, base))
