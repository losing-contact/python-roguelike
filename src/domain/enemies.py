"""Поведение врагов вне погони, невидимость привидения и маскировка мимика."""
from __future__ import annotations

import random

from domain.balance import GHOST_INVISIBLE_TURNS, GHOST_VISIBLE_TURNS
from domain.entities import Enemy, EnemyKind
from domain.items import ItemType
from domain.level import Level, Pos, Tile


def random_walk(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Случайный шаг по комнате (в коридоре - по любой проходимой клетке)."""
    in_room = level.tile_at(enemy.pos) is Tile.FLOOR
    options = [
        p for p in enemy.pos.neighbors()
        if level.can_enemy_enter(p) and (not in_room or level.tile_at(p) is Tile.FLOOR)
    ]
    return rng.choice(options) if options else None


def room_cells(level: Level, start: Pos) -> list[Pos]:
    """Клетки пола комнаты, где стоит start (заливка по Tile.FLOOR)."""
    seen = {start}
    stack = [start]
    while stack:
        cell = stack.pop()
        for neighbor in cell.neighbors():
            if neighbor not in seen and level.tile_at(neighbor) is Tile.FLOOR:
                seen.add(neighbor)
                stack.append(neighbor)
    return list(seen)


def teleport(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Прыжок на случайную свободную клетку той же комнаты (привидение)."""
    if level.tile_at(enemy.pos) is not Tile.FLOOR:
        return random_walk(enemy, level, rng)      # в коридоре - обычный шаг
    options = [
        p for p in room_cells(level, enemy.pos)
        if p != enemy.pos and level.can_enemy_enter(p)
    ]
    return rng.choice(options) if options else None


def two_step_walk(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Шаг на две клетки: сначала соседняя клетка, потом ещё одна от неё (огр)."""
    in_room = level.tile_at(enemy.pos) is Tile.FLOOR

    def ok(p: Pos) -> bool:
        return level.can_enemy_enter(p) and (not in_room or level.tile_at(p) is Tile.FLOOR)

    options = [
        second
        for first in enemy.pos.neighbors() if ok(first)
        for second in first.neighbors() if second != enemy.pos and ok(second)
    ]
    return rng.choice(options) if options else random_walk(enemy, level, rng)

DIAGONALS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def diagonal_walk(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """Выбирает другую диагональ, если она доступна (змей-маг)."""
    in_room = level.tile_at(enemy.pos) is Tile.FLOOR
    options = [
        p for p in (enemy.pos.shifted(dx, dy) for dx, dy in DIAGONALS)
        if level.can_enemy_enter(p) and (not in_room or level.tile_at(p) is Tile.FLOOR)
    ]
    if not options:
        return random_walk(enemy, level, rng)
    other_directions = [
        p for p in options
        if (p.x - enemy.pos.x, p.y - enemy.pos.y) != enemy.last_diagonal
    ]
    return rng.choice(other_directions or options)

PATTERNS = {
    EnemyKind.ZOMBIE: random_walk,
    EnemyKind.VAMPIRE: random_walk,
    EnemyKind.GHOST: teleport,
    EnemyKind.OGRE: two_step_walk,
    EnemyKind.WIZZARD: diagonal_walk,
    EnemyKind.MIMIC: random_walk,
}


def update_ghost_visibility(enemy: Enemy, rng: random.Random) -> None:
    """До первой атаки чередует фазы, после начала боя привидение всегда видно."""
    if enemy.kind is not EnemyKind.GHOST:
        return
    if enemy.combat_started:
        enemy.invisible = False
        return
    enemy.phase_turns -= 1
    if enemy.phase_turns <= 0:
        enemy.invisible = not enemy.invisible
        low, high = GHOST_INVISIBLE_TURNS if enemy.invisible else GHOST_VISIBLE_TURNS
        enemy.phase_turns = rng.randint(low, high)


# какие предметы бывают на карте (сокровища на полу не лежат, их не имитируем)
DISGUISES = (ItemType.FOOD, ItemType.ELIXIR, ItemType.SCROLL, ItemType.WEAPON)


def disguise_of(enemy: Enemy) -> ItemType:
    """Под какой предмет маскируется мимик (зависит от клетки, где он лежит)."""
    return DISGUISES[(enemy.pos.x * 3 + enemy.pos.y * 5) % len(DISGUISES)]
