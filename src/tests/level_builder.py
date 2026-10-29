"""Помощник для тестов: собирает маленький уровень из ASCII-картинки.

Обозначения: '#' стена, '.' пол, ':' коридор, '+' проём, '>' выход, ' ' порода, '@' старт (пол).
Цифра '0'-'9' - пол комнаты с таким номером (прямоугольник, у него будет объект Room).
'r', 'y', 'b' - проём с запертой дверью (красной, жёлтой, синей), 'R', 'Y', 'B' - ключ на полу.
"""
from __future__ import annotations

from domain.models.keys import KeyColor
from domain.models.level import Level, Room
from domain.models.position import Pos
from domain.models.tile import Tile

CHARS = {
    "#": Tile.WALL, ".": Tile.FLOOR, ":": Tile.CORRIDOR, "+": Tile.DOORWAY,
    ">": Tile.EXIT, " ": Tile.VOID, "@": Tile.FLOOR,
}


DOORS = {"r": KeyColor.RED, "y": KeyColor.YELLOW, "b": KeyColor.BLUE}
KEYS = {"R": KeyColor.RED, "Y": KeyColor.YELLOW, "B": KeyColor.BLUE}


def level_from_ascii(rows: list[str], number: int = 1, start: Pos | None = None) -> Level:
    exit_pos = None
    doors: dict[Pos, KeyColor] = {}
    keys: dict[Pos, KeyColor] = {}
    room_cells: dict[int, list[Pos]] = {}
    tiles = []
    for y, row in enumerate(rows):
        line = []
        for x, ch in enumerate(row):
            if ch in DOORS:
                line.append(Tile.DOORWAY)
                doors[Pos(x, y)] = DOORS[ch]
                continue
            if ch in KEYS:
                line.append(Tile.FLOOR)
                keys[Pos(x, y)] = KEYS[ch]
                continue
            if ch.isdigit():
                line.append(Tile.FLOOR)
                room_cells.setdefault(int(ch), []).append(Pos(x, y))
                continue
            line.append(CHARS[ch])
            if ch == "@" and start is None:
                start = Pos(x, y)
            if ch == ">":
                exit_pos = Pos(x, y)
        tiles.append(line)
    if start is None:
        start = Pos(0, 0)
    width = max(len(r) for r in rows)
    for line in tiles:
        line.extend([Tile.VOID] * (width - len(line)))
    return Level(
        number=number, width=width, height=len(rows), tiles=tiles,
        rooms=_rooms(room_cells), corridors=[], doors=doors, keys=keys,
        start=start, exit=exit_pos or Pos(-1, -1), start_room=0, exit_room=0,
    )


def _rooms(room_cells: dict[int, list[Pos]]) -> list[Room]:
    rooms = []
    for room_id, cells in sorted(room_cells.items()):
        xs, ys = [c.x for c in cells], [c.y for c in cells]
        room = Room(room_id, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, 0, 0)
        assert len(cells) == room.w * room.h, f"комната {room_id} не прямоугольная"
        rooms.append(room)
    return rooms


REVERSE = {Tile.WALL: "#", Tile.FLOOR: ".", Tile.CORRIDOR: ":", Tile.DOORWAY: "+", Tile.EXIT: ">"}


def picture(level: Level, visible: set[Pos], player: Pos | None = None) -> list[str]:
    """Рисует только видимые клетки (остальное - пробелы): удобно сравнивать с ожидаемым."""
    rows = []
    for y in range(level.height):
        row = ""
        for x in range(level.width):
            pos = Pos(x, y)
            if pos == player:
                row += "@"
            elif pos in visible:
                row += REVERSE.get(level.tile_at(pos), " ")
            else:
                row += " "
        rows.append(row.rstrip())
    return rows
