"""Команды: то, что игрок просит сделать. Presentation создаёт, domain выполняет."""
from __future__ import annotations

from dataclasses import dataclass

from domain.models.items import ItemType


@dataclass(frozen=True)
class Move:
    dx: int
    dy: int


@dataclass(frozen=True)
class UseItem:
    """Применить предмет из рюкзака. slot - номер с нуля; None - убрать оружие из рук."""

    item_type: ItemType
    slot: int | None


Command = Move | UseItem
