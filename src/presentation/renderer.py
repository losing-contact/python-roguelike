"""Рисует состояние игры. Читает сессию и ничего в ней не меняет."""
from __future__ import annotations

import curses

from domain.session import GameSession
from presentation.colors import Color, attr
from presentation.messages import item_label
from presentation.theme import (
    ENEMY_GLYPHS,
    ITEM_GLYPHS,
    PLAYER_GLYPH_CHAR,
    TILE_GLYPHS,
    Glyph,
)

HELP = "WASD ход  h оружие  j еда  k эликсир  e свиток  q выход"


def put(screen, y: int, x: int, text: str, style: int = 0) -> None:
    """addstr, который не падает на краю экрана."""
    rows, cols = screen.getmaxyx()
    if not (0 <= y < rows and 0 <= x < cols - 1):
        return
    try:
        screen.addstr(y, x, text[: cols - 1 - x], style)
    except curses.error:
        pass


def put_glyph(screen, y: int, x: int, glyph: Glyph) -> None:
    put(screen, y, x, glyph.char, attr(glyph.color, glyph.extra))


def draw(screen, session: GameSession, messages: list[str]) -> None:
    screen.erase()
    level = session.level

    for y, row in enumerate(level.tiles):
        for x, tile in enumerate(row):
            glyph = TILE_GLYPHS.get(tile)
            if glyph:
                put_glyph(screen, y, x, glyph)
    for pos, item in level.items.items():
        put_glyph(screen, pos.y, pos.x, ITEM_GLYPHS[item.item_type])
    for enemy in level.enemies:
        put_glyph(screen, enemy.pos.y, enemy.pos.x, ENEMY_GLYPHS[enemy.kind])
    p = session.player
    put(screen, p.pos.y, p.pos.x, PLAYER_GLYPH_CHAR, attr(Color.WALL, curses.A_BOLD))

    draw_status(screen, session, level.height)
    put(screen, level.height + 1, 0, "  |  ".join(messages[-2:]))
    put(screen, level.height + 2, 0, HELP, attr(Color.WALL, curses.A_DIM))
    screen.refresh()


def draw_status(screen, session: GameSession, row: int) -> None:
    p = session.player
    bar = "█" * p.health_blocks + "·" * max(0, p.max_blocks - p.health_blocks)
    weapon = f"  Оружие: {item_label(p.weapon)}" if p.weapon else ""
    text = (
        f"HP [{bar}] {p.health}/{p.max_health}  Сила {p.strength}  Ловк. {p.agility}"
        f"  Ур. {session.level.number}/{session.total_levels}"
        f"  Сокр. {p.backpack.treasure}{weapon}"
    )
    put(screen, row, 0, text, attr(Color.GREEN if p.health * 3 > p.max_health else Color.RED))
