"""Что видит игрок прямо сейчас (туман войны).

Правила из задания:
1. Внутри комнаты видна вся комната целиком: стены, пол, проёмы.
2. В коридоре (и в проёме) видна только область прямой видимости.
   Её находит ray casting: из клетки игрока пускаем лучи ко всем клеткам вокруг,
   а клетки вдоль луча получаем алгоритмом Брезенхэма. Луч останавливается на стене.

Функция чистая: смотрит на уровень и позицию, ничего не меняет.
"""
from __future__ import annotations

from domain.balance import VISION_RADIUS
from domain.geometry import bresenham
from domain.level import Level, Pos, Room, Tile

OPAQUE = frozenset({Tile.WALL, Tile.VOID})  # стены и порода не пропускают взгляд


def compute_visible(level: Level, pos: Pos, radius: int = VISION_RADIUS) -> set[Pos]:
    """Множество клеток, которые игрок в позиции pos видит прямо сейчас."""
    room = level.room_at(pos)
    if room is not None:
        return room_in_sight(level, room)
    return cast_rays(level, pos, radius)


def room_in_sight(level: Level, room: Room) -> set[Pos]:
    return {cell for cell in room.footprint() if level.in_bounds(cell)}


def blocks_sight(level: Level, pos: Pos) -> bool:
    return level.tile_at(pos) in OPAQUE or pos in level.doors


def cast_rays(level: Level, origin: Pos, radius: int) -> set[Pos]:
    """Ray casting: по лучу к каждой клетке круга радиуса radius, пока не упрёмся в стену."""
    visible = {origin}
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius:
                continue
            previous = origin
            for cell in bresenham(origin, origin.shifted(dx, dy)):
                if not level.in_bounds(cell):
                    break
                if cell.x != previous.x and cell.y != previous.y:
                    # Между двумя соприкасающимися преградами нет щели для взгляда.
                    if (blocks_sight(level, Pos(cell.x, previous.y))
                            and blocks_sight(level, Pos(previous.x, cell.y))):
                        break
                visible.add(cell)
                if blocks_sight(level, cell) and cell != origin:
                    break  # стену или дверь видим, а то, что за ними — нет
                previous = cell
    return visible
