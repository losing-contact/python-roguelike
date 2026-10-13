"""Помощник для тестов: собирает маленький уровень из ASCII-картинки.

Обозначения: '#' стена, '.' пол, ':' коридор, '+' проём, '>' выход, ' ' порода, '@' старт (пол).
"""
from __future__ import annotations

from domain.models.level import Level
from domain.models.position import Pos
from domain.models.tile import Tile

CHARS = {
    "#": Tile.WALL, ".": Tile.FLOOR, ":": Tile.CORRIDOR, "+": Tile.DOORWAY,
    ">": Tile.EXIT, " ": Tile.VOID, "@": Tile.FLOOR,
}


def level_from_ascii(rows: list[str], number: int = 1) -> Level:
    start = exit_pos = None
    tiles = []
    for y, row in enumerate(rows):
        line = []
        for x, ch in enumerate(row):
            line.append(CHARS[ch])
            if ch == "@":
                start = Pos(x, y)
            if ch == ">":
                exit_pos = Pos(x, y)
        tiles.append(line)
    assert start is not None, "в картинке нужен '@'"
    width = max(len(r) for r in rows)
    for line in tiles:
        line.extend([Tile.VOID] * (width - len(line)))
    return Level(
        number=number, width=width, height=len(rows), tiles=tiles, rooms=[], corridors=[],
        start=start, exit=exit_pos or Pos(-1, -1), start_room=0, exit_room=0,
    )
