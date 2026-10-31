"""Оформление игры: цвета, символы и их инициализация в curses."""
from __future__ import annotations

import curses
from enum import IntEnum
from typing import NamedTuple

from domain.entities import EnemyKind
from domain.items import ItemType
from domain.level import KeyColor, Tile


class Color(IntEnum):
    """Номера цветовых пар curses."""

    DEFAULT = 0
    WALL = 1
    RED = 2
    GREEN = 3
    YELLOW = 4
    CYAN = 5
    MAGENTA = 6
    BLUE = 7


def init_colors() -> None:
    """Только 8 базовых цветов: работает в любом терминале."""
    if not curses.has_colors():
        return
    curses.start_color()
    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = curses.COLOR_BLACK
    curses.init_pair(Color.WALL, curses.COLOR_WHITE, background)
    curses.init_pair(Color.RED, curses.COLOR_RED, background)
    curses.init_pair(Color.GREEN, curses.COLOR_GREEN, background)
    curses.init_pair(Color.YELLOW, curses.COLOR_YELLOW, background)
    curses.init_pair(Color.CYAN, curses.COLOR_CYAN, background)
    curses.init_pair(Color.MAGENTA, curses.COLOR_MAGENTA, background)
    curses.init_pair(Color.BLUE, curses.COLOR_BLUE, background)


def attr(color: Color, extra: int = 0) -> int:
    return curses.color_pair(color) | extra


class Glyph(NamedTuple):
    """Символ и цвет. Стиль curses считается при отрисовке: color_pair нужен initscr()."""

    char: str
    color: Color
    extra: int = 0   # дополнительные атрибуты: curses.A_BOLD, curses.A_DIM


TILE_GLYPHS: dict[Tile, Glyph] = {
    Tile.WALL: Glyph("█", Color.WALL, curses.A_DIM),
    Tile.FLOOR: Glyph(".", Color.WALL, curses.A_DIM),
    Tile.DOORWAY: Glyph("+", Color.WALL, curses.A_DIM),
    Tile.CORRIDOR: Glyph("░", Color.WALL),
    Tile.EXIT: Glyph(">", Color.CYAN, curses.A_BOLD),
}

ENEMY_GLYPHS: dict[EnemyKind, Glyph] = {
    EnemyKind.ZOMBIE: Glyph("z", Color.GREEN),
    EnemyKind.VAMPIRE: Glyph("v", Color.RED),
    EnemyKind.GHOST: Glyph("g", Color.WALL, curses.A_BOLD),
    EnemyKind.OGRE: Glyph("O", Color.YELLOW, curses.A_BOLD),
    EnemyKind.WIZZARD: Glyph("s", Color.WALL, curses.A_BOLD),
    EnemyKind.MIMIC: Glyph("m", Color.WALL, curses.A_BOLD),
}

ITEM_GLYPHS: dict[ItemType, Glyph] = {
    ItemType.FOOD: Glyph("❤︎", Color.GREEN, curses.A_BOLD),
    ItemType.ELIXIR: Glyph("𐃯", Color.MAGENTA),
    ItemType.SCROLL: Glyph("🕮", Color.YELLOW, curses.A_DIM),
    ItemType.WEAPON: Glyph("༒︎", Color.WALL, curses.A_DIM),
    ItemType.TREASURE: Glyph("$", Color.YELLOW, curses.A_BOLD),
}

KEY_CHAR = "="
DOOR_CHAR = "▒"
KEY_COLORS = {KeyColor.RED: Color.RED, KeyColor.YELLOW: Color.YELLOW, KeyColor.BLUE: Color.BLUE}

PLAYER_GLYPH_CHAR = "@"
# Что остаётся нарисованным на уже невидимых, но увиденных ранее клетках.
REMEMBERED_TILES = frozenset({Tile.WALL, Tile.DOORWAY, Tile.CORRIDOR})
