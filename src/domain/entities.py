"""Игрок и враги: характеристики, состояние и создание противников."""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from domain.balance import (
    ENEMY_GROWTH,
    GHOST_CHANCE,
    MIMIC_CHANCE,
    MIN_HEALTH_AFTER_EFFECT,
    MIN_MAX_HEALTH,
    OGRE_CHANCE,
    PLAYER_AGILITY,
    PLAYER_MAX_HEALTH,
    PLAYER_STRENGTH,
    SCALE,
    VAMPIRE_CHANCE_MAX,
    VAMPIRE_CHANCE_START,
    VAMPIRE_CHANCE_STEP,
    WIZZARD_CHANCE,
)
from domain.items import Backpack, Item, Stat
from domain.level import KeyColor, Pos


class EnemyKind(Enum):
    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    GHOST = "ghost"
    OGRE = "ogre"
    WIZZARD = "wizzard"
    MIMIC = "mimic"


@dataclass(frozen=True)
class EnemySpec:
    kind: EnemyKind
    name: str
    max_health: int
    agility: int
    strength: int
    hostility: int             # с какого расстояния (по пути) начинается преследование
    move_every: int = 1        # враг действует раз в N ходов игрока

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
    ),
    EnemyKind.GHOST: EnemySpec(
        EnemyKind.GHOST, "Привидение",
        max_health=2 * SCALE, agility=8, strength=SCALE // 2,
        hostility=3, move_every=2,
    ),
    EnemyKind.OGRE: EnemySpec(
        EnemyKind.OGRE, "Огр",
        max_health=10 * SCALE, agility=2, strength=3 * SCALE,
        hostility=5, move_every=3,
    ),
    EnemyKind.WIZZARD: EnemySpec(
        EnemyKind.WIZZARD, "Змей-маг",
        max_health=5 * SCALE, agility=10, strength=1 * SCALE,
        hostility=8, move_every=2,
    ),

    EnemyKind.MIMIC: EnemySpec(
        EnemyKind.MIMIC, "Мимик",
        max_health=10 * SCALE, agility=8, strength=1 * SCALE,
        hostility=2, move_every=2,
    ),

}


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
    kind: EnemyKind | None = None  # у игрока нет типа противника

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def attack_power(self) -> int:
        return self.strength


    @property
    def health_blocks(self) -> int:
        """Блоков полоски здоровья; минимум 1, пока жив."""
        return (self.health + SCALE - 1) // SCALE  # деление с округлением вверх

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
        self.keys: set[KeyColor] = set()
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
    first_hit_spent: bool = False  # вампир: первый удар уже «промазан»

    invisible: bool = False
    phase_turns: int = 3
    combat_started: bool = False  # привидение больше не скрывается после начала боя
    resting: bool = False
    counter_ready: bool = False
    disguised: bool = False
    last_diagonal: tuple[int, int] | None = None  # последнее направление змея-мага

    @property
    def kind(self) -> EnemyKind:
        return self.spec.kind

    @property
    def hostility(self) -> int:
        return self.spec.hostility


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
        disguised=kind is EnemyKind.MIMIC,     # мимик лежит под видом предмета
    )


def pick_enemy_kind(level: int, rng: random.Random) -> EnemyKind:
    """Чем глубже уровень, тем чаще встречаются сильные враги."""
    vampire_chance = min(
        VAMPIRE_CHANCE_MAX, VAMPIRE_CHANCE_START + VAMPIRE_CHANCE_STEP * (level - 1)
    )
    roll = rng.random()
    if roll < vampire_chance:
        return EnemyKind.VAMPIRE
    if roll < vampire_chance + GHOST_CHANCE:
        return EnemyKind.GHOST
    if roll < vampire_chance + GHOST_CHANCE + OGRE_CHANCE:
        return EnemyKind.OGRE
    if roll < vampire_chance + GHOST_CHANCE + OGRE_CHANCE + WIZZARD_CHANCE:
        return EnemyKind.WIZZARD
    if roll < vampire_chance + GHOST_CHANCE + OGRE_CHANCE + WIZZARD_CHANCE + MIMIC_CHANCE:
        return EnemyKind.MIMIC

    return EnemyKind.ZOMBIE
