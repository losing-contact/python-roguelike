import curses

from presentation.colors import Color, attr
from presentation.input import normalize, read_key
from presentation.renderer import put

ITEMS = [
    ("new", "Новая игра"),
    ("continue", "Продолжить"),
    ("records", "Таблица рекордов"),
    ("quit", "Выход"),
]


def choose(screen, can_continue):
    """Показывает главное меню и возвращает выбор: "new", "continue", "records" или "quit"."""
    index = 1 if can_continue else 0   # если есть сохранение, сразу стоим на «Продолжить»
    while True:
        draw(screen, index, can_continue)
        key = normalize(read_key(screen))
        if key in ("w", curses.KEY_UP):
            index = next_index(index, -1, can_continue)
        elif key in ("s", curses.KEY_DOWN):
            index = next_index(index, 1, can_continue)
        elif key in ("\n", "\r", curses.KEY_ENTER):
            return ITEMS[index][0]
        elif key == "q":
            return "quit"


def next_index(index, step, can_continue):
    """Соседний пункт меню (step = 1 вниз, -1 вверх). Недоступное «Продолжить» пропускаем."""
    while True:
        index = (index + step) % len(ITEMS)
        if ITEMS[index][0] != "continue" or can_continue:
            return index