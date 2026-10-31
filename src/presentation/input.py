"""Клавиатура -> запросы к игре. Единственное место, где известны клавиши."""
from __future__ import annotations

import curses
from dataclasses import dataclass

from domain.commands import Move
from domain.items import ItemType

# То же, что w/a/s/d/h/j/k/e/q, но на русской раскладке.
RU_LAYOUT = {"ц": "w", "ф": "a", "ы": "s", "в": "d", "р": "h", "о": "j", "л": "k", "у": "e",
             "й": "q"}

MOVES = {"w": (0, -1), "a": (-1, 0), "s": (0, 1), "d": (1, 0)}
ARROWS = {
    curses.KEY_UP: (0, -1), curses.KEY_LEFT: (-1, 0),
    curses.KEY_DOWN: (0, 1), curses.KEY_RIGHT: (1, 0),
}
MENUS = {
    "h": ItemType.WEAPON, "j": ItemType.FOOD, "k": ItemType.ELIXIR, "e": ItemType.SCROLL,
}


@dataclass(frozen=True)
class OpenMenu:
    """Игрок хочет выбрать предмет этого типа из рюкзака."""

    item_type: ItemType


@dataclass(frozen=True)
class Quit:
    pass


Key = str | int


def read_key(screen) -> Key:
    """Читает нажатие: символ (str) или код специальной клавиши (int)."""
    try:
        return screen.get_wch()
    except curses.error:
        return -1


def normalize(key: Key) -> Key:
    if isinstance(key, str):
        key = key.lower()
        return RU_LAYOUT.get(key, key)
    return key


def translate(key: Key) -> Move | OpenMenu | Quit | None:
    key = normalize(key)
    if key in ARROWS:
        return Move(*ARROWS[key])
    if isinstance(key, str):
        if key in MOVES:
            return Move(*MOVES[key])
        if key in MENUS:
            return OpenMenu(MENUS[key])
        if key == "q":
            return Quit()
    return None
