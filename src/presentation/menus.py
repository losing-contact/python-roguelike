"""Главное меню и выбор предмета из рюкзака."""
from __future__ import annotations

import curses

from domain.commands import UseItem
from domain.entities import Character
from domain.items import ItemType
from presentation.input import normalize, read_key
from presentation.messages import ITEM_TYPE_TITLES, item_label
from presentation.renderer import put
from presentation.theme import Color, attr

ITEMS = [
    ("new", "Новая игра"),
    ("continue", "Продолжить"),
    ("records", "Таблица рекордов"),
    ("quit", "Выход"),
]


def draw_menu(screen, index, can_continue):
    """Отрисовка главного меню."""
    screen.clear()   # полная перерисовка
    rows, cols = screen.getmaxyx()
    width = max(len(text) for _, text in ITEMS) + 2
    left = (cols - width) // 2
    top = rows // 2 - 4

    title = "R O G U E"
    put(screen, top, (cols - len(title)) // 2, title, attr(Color.CYAN, curses.A_BOLD))

    for i, (name, text) in enumerate(ITEMS):
        if name == "continue" and not can_continue:
            style = attr(Color.WALL, curses.A_DIM)       # недоступно
        elif i == index:
            style = attr(Color.GREEN, curses.A_REVERSE)  # выбранный пункт
        else:
            style = attr(Color.WALL)
        line = ("> " if i == index else "  ") + text
        put(screen, top + 2 + i, left, line.ljust(width), style)

    hint = "W/S или стрелки - выбор, Enter - выбрать, q - выход"
    put(screen, top + 3 + len(ITEMS), (cols - len(hint)) // 2, hint,
        attr(Color.WALL, curses.A_DIM))
    screen.refresh()


def choose_main(screen, can_continue):
    """Показывает главное меню и возвращает выбор: "new", "continue", "records" или "quit"."""
    index = 1 if can_continue else 0   # если есть сохранение, сразу стоим на «Продолжить»
    while True:
        draw_menu(screen, index, can_continue)
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


def choose_item(screen, player: Character, item_type: ItemType) -> UseItem | None:
    """Показывает список предметов типа и ждёт выбор. None - игрок передумал."""
    items = player.backpack.items_of(item_type)
    is_weapon = item_type is ItemType.WEAPON
    lines = [f"{ITEM_TYPE_TITLES[item_type]}: выберите номер, Esc - отмена", ""]
    if is_weapon:
        current = item_label(player.weapon) if player.weapon else "пусто"
        lines.append(f"0) убрать оружие из рук (сейчас: {current})")
    lines += [f"{i}) {item_label(item)}" for i, item in enumerate(items, start=1)]
    if not items and not is_weapon:
        lines.append("(пусто)")

    _draw_popup(screen, lines)
    key = read_key(screen)
    if isinstance(key, str) and key.isdigit():
        number = int(key)
        if number == 0 and is_weapon:
            return UseItem(item_type, None)
        if 1 <= number <= len(items):
            return UseItem(item_type, number - 1)
    return None


def _draw_popup(screen, lines: list[str]) -> None:
    rows, cols = screen.getmaxyx()
    width = min(cols - 2, max(len(line) for line in lines) + 4)
    height = len(lines) + 2
    top = max(0, (rows - height) // 2)
    left = max(0, (cols - width) // 2)
    border = attr(Color.YELLOW)
    put(screen, top, left, "┌" + "─" * (width - 2) + "┐", border)
    for i, line in enumerate(lines, start=1):
        put(screen, top + i, left, "│" + " " * (width - 2) + "│", border)
        put(screen, top + i, left + 2, line)
    put(screen, top + height - 1, left, "└" + "─" * (width - 2) + "┘", border)
    screen.refresh()
    curses.flushinp()
