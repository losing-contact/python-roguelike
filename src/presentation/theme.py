"""Как выглядят сущности на экране: символ и цвет. Всё про внешний вид - только здесь."""
import curses
from typing import NamedTuple

from domain.enemies.types import EnemyKind
from domain.models.items import ItemType
from domain.models.tile import Tile
from presentation.colors import Color


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
    EnemyKind.GHOST: Glyph("g", Color.CYAN, curses.A_DIM),
}

ITEM_GLYPHS: dict[ItemType, Glyph] = {
    ItemType.FOOD: Glyph("❤︎", Color.GREEN, curses.A_BOLD),
    ItemType.ELIXIR: Glyph("𐃯", Color.MAGENTA),
    ItemType.SCROLL: Glyph("🕮", Color.YELLOW, curses.A_DIM),
    ItemType.WEAPON: Glyph("༒︎", Color.WALL, curses.A_DIM),
    ItemType.TREASURE: Glyph("$", Color.YELLOW, curses.A_BOLD),
}

PLAYER_GLYPH_CHAR = "@"
# Что остаётся нарисованным на уже невидимых, но увиденных ранее клетках.
REMEMBERED_TILES = frozenset({Tile.WALL, Tile.DOORWAY, Tile.CORRIDOR})