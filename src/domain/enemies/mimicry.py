"""Мимик: пока маска не спала, на карте выглядит как предмет."""
from __future__ import annotations

from domain.models.entities import Enemy
from domain.models.items import ItemType

# какие предметы бывают на карте (сокровища на полу не лежат, их не имитируем)
DISGUISES = (ItemType.FOOD, ItemType.ELIXIR, ItemType.SCROLL, ItemType.WEAPON)


def disguise_of(enemy: Enemy) -> ItemType:
    """Под какой предмет маскируется мимик (зависит от клетки, где он лежит)."""
    return DISGUISES[(enemy.pos.x * 3 + enemy.pos.y * 5) % len(DISGUISES)]