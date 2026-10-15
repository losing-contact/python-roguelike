"""Невидимость привидения: периодически пропадает, пока игрок не вступил в бой."""
from __future__ import annotations

import random

from domain.balance import GHOST_INVISIBLE_TURNS, GHOST_VISIBLE_TURNS
from domain.enemies.types import Trait
from domain.models.entities import Enemy
from domain.models.position import Pos


def tick(enemy: Enemy, player_pos: Pos, rng: random.Random) -> None:
    """Вызывать в начале хода врага. Бой = привидение рядом с игроком: тогда оно видно."""
    if Trait.INVISIBLE_PHASES not in enemy.spec.traits:
        return
    if enemy.pos in player_pos.neighbors():
        enemy.invisible = False
        enemy.phase_turns = rng.randint(*GHOST_VISIBLE_TURNS)   # после боя ещё побудет видимым
        return
    enemy.phase_turns -= 1
    if enemy.phase_turns <= 0:
        enemy.invisible = not enemy.invisible
        low, high = GHOST_INVISIBLE_TURNS if enemy.invisible else GHOST_VISIBLE_TURNS
        enemy.phase_turns = rng.randint(low, high)
