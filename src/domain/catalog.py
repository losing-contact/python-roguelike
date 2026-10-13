"""Каталог предметов: из каких шаблонов генератор собирает содержимое уровней."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from domain.models.items import Item, ItemType


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
