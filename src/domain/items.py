"""Предметы: рюкзак, характеристики и шаблоны генерации."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from domain.balance import BACKPACK_SLOT_LIMIT


class ItemType(Enum):
    TREASURE = "treasure"
    FOOD = "food"
    ELIXIR = "elixir"
    SCROLL = "scroll"
    WEAPON = "weapon"


class Stat(Enum):
    MAX_HEALTH = "max_health"
    AGILITY = "agility"
    STRENGTH = "strength"


@dataclass
class Item:
    """Предмет. Заполнены только те числа, которые к нему относятся."""

    item_type: ItemType
    subtype: str                # человекочитаемое название: «Меч», «Свиток силы»...
    health: int = 0             # еда: на сколько восстанавливает здоровье
    max_health: int = 0         # эликсир/свиток: прибавка к максимальному здоровью
    agility: int = 0            # эликсир/свиток: прибавка к ловкости
    strength: int = 0           # эликсир/свиток/оружие: прибавка к силе
    cost: int = 0               # сокровища: стоимость
    duration: int = 0           # эликсир: сколько ходов действует

    def stat_bonus(self) -> tuple[Stat, int]:
        """Какая характеристика и на сколько повышается (эликсиры и свитки)."""
        if self.max_health:
            return Stat.MAX_HEALTH, self.max_health
        if self.agility:
            return Stat.AGILITY, self.agility
        if self.strength:
            return Stat.STRENGTH, self.strength
        raise ValueError(f"У предмета {self.subtype!r} нет бонуса к характеристике")


class Backpack:
    """До 9 предметов каждого типа; сокровища копятся в единственной ячейке."""

    def __init__(self) -> None:
        self.treasure = 0
        self._slots: dict[ItemType, list[Item]] = {
            t: [] for t in ItemType if t is not ItemType.TREASURE
        }

    def is_full(self, item_type: ItemType) -> bool:
        return len(self._slots[item_type]) >= BACKPACK_SLOT_LIMIT

    def add(self, item: Item) -> bool:
        """Кладёт предмет в рюкзак. False - если для этого типа нет места."""
        if item.item_type is ItemType.TREASURE:
            self.treasure += item.cost
            return True
        if self.is_full(item.item_type):
            return False
        self._slots[item.item_type].append(item)
        return True

    def items_of(self, item_type: ItemType) -> list[Item]:
        return list(self._slots[item_type])

    def take(self, item_type: ItemType, index: int) -> Item | None:
        """Достаёт предмет по индексу (с нуля). None - если такого нет."""
        slot = self._slots[item_type]
        if 0 <= index < len(slot):
            return slot.pop(index)
        return None


@dataclass(frozen=True)
class ItemTemplate:
    item_type: ItemType
    subtype: str
    weight: int                                   # относительная частота появления
    ranges: dict[str, tuple[int, int]] = field(default_factory=dict)  # поле Item -> (мин, макс)
    duration: int = 0                             # для эликсиров


ITEM_TEMPLATES: list[ItemTemplate] = [
    ItemTemplate(ItemType.FOOD, "Яблоко", 3, {"health": (15, 25)}),
    ItemTemplate(ItemType.FOOD, "Рацион", 2, {"health": (30, 40)}),
    ItemTemplate(ItemType.ELIXIR, "Эликсир силы", 1, {"strength": (10, 20)}, duration=30),
    ItemTemplate(ItemType.ELIXIR, "Эликсир ловкости", 1, {"agility": (1, 3)}, duration=30),
    ItemTemplate(ItemType.ELIXIR, "Эликсир стойкости", 1, {"max_health": (20, 40)}, duration=30),
    ItemTemplate(ItemType.SCROLL, "Свиток силы", 1, {"strength": (5, 10)}),
    ItemTemplate(ItemType.SCROLL, "Свиток ловкости", 1, {"agility": (1, 1)}),
    ItemTemplate(ItemType.SCROLL, "Свиток жизни", 1, {"max_health": (10, 20)}),
    ItemTemplate(ItemType.WEAPON, "Кинжал", 1, {"strength": (5, 8)}),
    ItemTemplate(ItemType.WEAPON, "Меч", 1, {"strength": (10, 15)}),
    ItemTemplate(ItemType.WEAPON, "Топор", 1, {"strength": (15, 20)}),
]

# типы, которые обязаны встретиться на каждом уровне хотя бы раз
GUARANTEED_TYPES = [ItemType.FOOD]


def roll_item(template: ItemTemplate, rng: random.Random) -> Item:
    values = {name: rng.randint(lo, hi) for name, (lo, hi) in template.ranges.items()}
    return Item(template.item_type, template.subtype, duration=template.duration, **values)


def random_template(rng: random.Random) -> ItemTemplate:
    return rng.choices(ITEM_TEMPLATES, weights=[t.weight for t in ITEM_TEMPLATES])[0]


def random_template_of_type(item_type: ItemType, rng: random.Random) -> ItemTemplate:
    pool = [t for t in ITEM_TEMPLATES if t.item_type is item_type]
    return rng.choices(pool, weights=[t.weight for t in pool])[0]
