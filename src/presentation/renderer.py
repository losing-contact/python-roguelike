"""Рисует состояние игры. Читает сессию и ничего в ней не меняет.

Раскладка (всё внутри одной рамки):

    ╔═[ Уровень 3 ]═════════════════╗
    ║  карта                         ║
    ╠════════════════════════════════╣
    ║  HP [█████░░░░░] 50/100  СИЛА  ║
    ╟────────────────────────────────╢
    ║  › старое сообщение            ║
    ║  › новое сообщение             ║
    ╟────────────────────────────────╢
    ║      WASD ход · h оружие ...   ║
    ╚════════════════════════════════╝
"""
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
    REMEMBERED_TILES,
)

HELP = "WASD ход · h оружие · j еда · k эликсир · e свиток · q выход"

STATUS_ROWS = 1
MESSAGE_ROWS = 2
# статус + разделитель + сообщения + разделитель + подсказка
HUD_ROWS = STATUS_ROWS + 1 + MESSAGE_ROWS + 1 + 1
EXTRA_ROWS = HUD_ROWS + 3                     # + верхняя рамка, разделитель карты, нижняя рамка
EXTRA_COLS = 3                                # две боковые рамки + столбец, куда curses не пишет


def put(screen, y: int, x: int, text: str, style: int = 0) -> None:
    """addstr, который не падает на краю экрана."""
    rows, cols = screen.getmaxyx()
    if not (0 <= y < rows and 0 <= x < cols - 1):
        return
    try:
        screen.addstr(y, x, text[: cols - 1 - x], style)
    except curses.error:
        pass


def put_glyph(screen, y: int, x: int, glyph: Glyph, dim: bool = False) -> None:
    extra = glyph.extra | curses.A_DIM if dim else glyph.extra
    put(screen, y, x, glyph.char, attr(glyph.color, extra))

def put_segments(screen, y: int, x: int, segments: list[tuple[str, int]], limit: int) -> None:
    """Куски текста разных стилей подряд, не длиннее limit символов."""
    for text, style in segments:
        if limit <= 0:
            return
        text = text[:limit]
        put(screen, y, x, text, style)
        x += len(text)
        limit -= len(text)


def draw(screen, session: GameSession, messages: list[str]) -> None:
    screen.erase()
    level = session.level
    h = len(level.tiles)
    w = len(level.tiles[0])

    visible = session.visible
    # 1. память: увиденное раньше, но не видимое сейчас
    for pos in session.exploration.seen - visible:
        tile = level.tile_at(pos)
        if tile in REMEMBERED_TILES:
            put_glyph(screen, pos.y, pos.x, TILE_GLYPHS[tile], dim=True)
    # 2. то, что видно прямо сейчас
    for pos in visible:
        glyph = TILE_GLYPHS.get(level.tile_at(pos))
        if glyph:
            put_glyph(screen, pos.y, pos.x, glyph)
    for pos, item in level.items.items():
        if pos in visible:
            put_glyph(screen, pos.y, pos.x, ITEM_GLYPHS[item.item_type])
    for enemy in level.enemies:
        if enemy.pos in visible:
            put_glyph(screen, enemy.pos.y, enemy.pos.x, ENEMY_GLYPHS[enemy.kind])
    p = session.player
    put(screen, p.pos.y + 1, p.pos.x + 1, PLAYER_GLYPH_CHAR, attr(Color.WALL, curses.A_BOLD))

    draw_frame(screen, session, h, w)
    draw_hud(screen, session, messages, h, w)
    screen.refresh()


def draw_frame(screen, session: GameSession, h: int, w: int) -> None:
    border = attr(Color.WALL, curses.A_BOLD)
    map_divider = h + 1
    status_divider = h + 2 + STATUS_ROWS
    help_divider = status_divider + MESSAGE_ROWS + 1
    bottom = h + HUD_ROWS + 2

    title = f" Уровень {session.level.number} "
    put(screen, 0, 0, "╔═[" + title + "]" + "═" * max(0, w - len(title) - 3) + "╗", border)
    put(screen, 0, 3, title, attr(Color.CYAN, curses.A_BOLD))

    for y in range(1, bottom):
        if y in (map_divider, status_divider, help_divider):
            continue
        put(screen, y, 0, "║", border)
        put(screen, y, w + 1, "║", border)
    put(screen, map_divider, 0, "╠" + "═" * w + "╣", border)
    for y in (status_divider, help_divider):
        put(screen, y, 0, "╟" + "─" * w + "╢", border)
    put(screen, bottom, 0, "╚" + "═" * w + "╝", border)


def draw_hud(screen, session: GameSession, messages: list[str], h: int, w: int) -> None:
    p = session.player
    x, limit = 2, max(0, w - 2)
    label = attr(Color.WALL, curses.A_DIM)
    normal = attr(Color.WALL)

    # --- статус в одну строку: здоровье, характеристики, сокровища, оружие ---
    ratio = p.health / p.max_health if p.max_health else 0
    hp_color = Color.GREEN if ratio > 0.5 else Color.YELLOW if ratio > 0.25 else Color.RED
    hp_style = attr(hp_color, curses.A_BOLD)
    gold = attr(Color.YELLOW, curses.A_BOLD)
    weapon = item_label(p.weapon) if p.weapon else "кулаки"
    put_segments(screen, h + 2, x, [
        ("HP ", label), ("[", label),
        ("█" * p.health_blocks, hp_style),
        ("░" * max(0, p.max_blocks - p.health_blocks), label),
        ("] ", label), (f"{p.health}/{p.max_health}", hp_style),
        ("   СИЛА ", label), (str(p.strength), attr(Color.RED, curses.A_BOLD)),
        ("   ЛОВК ", label), (str(p.agility), attr(Color.CYAN, curses.A_BOLD)),
        ("   * ", gold), (str(p.backpack.treasure), gold),
        ("   ОРУЖИЕ ", label), (weapon, normal),   # длинное название обрежется, а не сломает рамку
    ], limit)

    # --- журнал: последние сообщения, новое внизу и ярче ---
    lines = ([""] * MESSAGE_ROWS + messages)[-MESSAGE_ROWS:]
    for i, text in enumerate(lines):
        if text:
            style = normal if i == len(lines) - 1 else label
            put_segments(screen, h + 2 + STATUS_ROWS + 1 + i, x,
                         [("› ", label), (text, style)], limit)

    # --- подсказка по клавишам: отдельная строка внутри рамки, по центру ---
    help_text = HELP[:limit]
    help_row = h + 2 + STATUS_ROWS + MESSAGE_ROWS + 2
    put(screen, help_row, 1 + (w - len(help_text)) // 2, help_text, label)