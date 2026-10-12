"""Меню выбора предмета из рюкзака (цифры 1-9, для оружия ещё 0 - убрать из рук)."""
from __future__ import annotations

import curses

from domain.commands import UseItem
from domain.models.entities import Character
from domain.models.items import ItemType
from presentation.colors import Color, attr
from presentation.input import read_key
from presentation.messages import ITEM_TYPE_TITLES, item_label
from presentation.renderer import put


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
