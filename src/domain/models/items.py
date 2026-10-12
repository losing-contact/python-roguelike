from __future__ import annotations

from dataclasses import dataclass
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
        for stat in Stat:
            amount = getattr(self, stat.value)
            if amount:
                return stat, amount
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
