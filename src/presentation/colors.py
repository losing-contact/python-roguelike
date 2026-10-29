import curses
from enum import IntEnum


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
