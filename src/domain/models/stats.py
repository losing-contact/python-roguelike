from __future__ import annotations

from dataclasses import dataclass

from domain import events as ev
from domain.models.items import ItemType


@dataclass
class RunStats:
    """Статистика одного прохождения. Заполняется из событий, а не из разбросанных счётчиков."""

    treasure: int = 0
    level_reached: int = 1
    enemies_killed: int = 0
    food_eaten: int = 0
    elixirs_drunk: int = 0
    scrolls_read: int = 0
    hits_dealt: int = 0
    hits_missed: int = 0
    steps: int = 0

    def record(self, event: ev.Event) -> None:
        match event:
            case ev.Moved():
                self.steps += 1
            case ev.PlayerAttacked(hit=hit):
                if hit:
                    self.hits_dealt += 1
                else:
                    self.hits_missed += 1
            case ev.EnemyKilled(treasure=treasure):
                self.enemies_killed += 1
                self.treasure += treasure
            case ev.ItemUsed(item=item):
                if item.item_type is ItemType.FOOD:
                    self.food_eaten += 1
                elif item.item_type is ItemType.ELIXIR:
                    self.elixirs_drunk += 1
                elif item.item_type is ItemType.SCROLL:
                    self.scrolls_read += 1
            case ev.LevelChanged(level=level):
                self.level_reached = level
