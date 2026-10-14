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
from domain.models.level import Level, Room
from domain.models.position import Pos
from domain.models.tile import Tile

OPAQUE = frozenset({Tile.WALL, Tile.VOID})  # стены и порода не пропускают взгляд


def compute_visible(level: Level, pos: Pos, radius: int = VISION_RADIUS) -> set[Pos]:
    """Множество клеток, которые игрок в позиции pos видит прямо сейчас."""
    room = level.room_at(pos)
    if room is not None:
        return room_in_sight(level, room)
    return cast_rays(level, pos, radius)


def room_in_sight(level: Level, room: Room) -> set[Pos]:
    return {cell for cell in room.footprint() if level.in_bounds(cell)}


def cast_rays(level: Level, origin: Pos, radius: int) -> set[Pos]:
    """Ray casting: по лучу к каждой клетке круга радиуса radius, пока не упрёмся в стену."""
    visible = {origin}
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius:
                continue
            for cell in bresenham(origin, origin.shifted(dx, dy)):
                if not level.in_bounds(cell):
                    break
                visible.add(cell)
                if level.tile_at(cell) in OPAQUE and cell != origin:
                    break  # стену видим, а то, что за ней - нет
    return visible
