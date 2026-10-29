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

from domain.models.position import Pos
from domain.session import GameSession
from presentation.colors import Color, attr
from presentation.menu_items import ITEMS
from presentation.messages import item_label
from presentation.theme import (
    DOOR_CHAR,
    ENEMY_GLYPHS,
    ITEM_GLYPHS,
    KEY_CHAR,
    KEY_COLORS,
    PLAYER_GLYPH_CHAR,
    REMEMBERED_TILES,
    TILE_GLYPHS,
    Glyph,
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

def put_map(screen, pos, glyph, dim=False):
    """Клетка карты на экране. Слева и сверху рамка, поэтому сдвиг на 1."""
    put_glyph(screen, pos.y + 1, pos.x + 1, glyph, dim)


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


def draw(screen, session: GameSession, messages: list[str]) -> None:
    """Полная отрисовка игрового процесса: рамка, HUD, карта, персонажи."""
    screen.clear()
    h, w = session.level.height, session.level.width

    # 1. Рисуем рамку и HUD
    draw_frame(screen, session, h, w)
    draw_hud(screen, session, messages, h, w)

    # 2. Отрисовка карты (тайлы)
    for y in range(session.level.height):
        for x in range(session.level.width):
            pos = Pos(x, y)

            if pos in session.visible:
                tile = session.level.tile_at(pos)
                glyph = TILE_GLYPHS.get(tile)
                if glyph:
                    put_map(screen, pos, glyph)
            elif pos in session.exploration.seen:
                tile = session.level.tile_at(pos)
                glyph = TILE_GLYPHS.get(tile) if tile in REMEMBERED_TILES else None
                if glyph:
                    put_map(screen, pos, glyph, dim=True)
    for pos, color in session.level.doors.items():
        if pos in session.exploration.seen:
            put_map(screen, pos, Glyph(DOOR_CHAR, KEY_COLORS[color], curses.A_BOLD),
                    dim=pos not in session.visible)
    for pos, color in session.level.keys.items():
        if pos in session.visible:
            put_map(screen, pos, Glyph(KEY_CHAR, KEY_COLORS[color], curses.A_BOLD))

    # 3. Отрисовка предметов
    for pos, item in session.level.items.items():
        if pos in session.visible:
            glyph = ITEM_GLYPHS.get(item.item_type)
            if glyph:
                put_map(screen, pos, glyph)

    # 4. Отрисовка врагов
    for enemy in session.level.enemies:
        if enemy.pos in session.visible and not enemy.invisible:
            glyph = ENEMY_GLYPHS.get(enemy.kind)
            if glyph:
                put_map(screen, enemy.pos, glyph)

    # 5. Отрисовка игрока
    if session.player:
        player_glyph = Glyph(PLAYER_GLYPH_CHAR, Color.YELLOW, curses.A_BOLD)
        put_map(screen, session.player.pos, player_glyph)

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
    keys = [(KEY_CHAR + " ", attr(KEY_COLORS[c], curses.A_BOLD))
            for c in sorted(p.keys, key=lambda c: c.value)]
    if keys:
        keys.insert(0, ("   КЛЮЧИ ", label))
    put_segments(screen, h + 2, x, [
        ("HP ", label), ("[", label),
        ("█" * p.health_blocks, hp_style),
        ("░" * max(0, p.max_blocks - p.health_blocks), label),
        ("] ", label), (f"{p.health}/{p.max_health}", hp_style), (" |", label),
        ("   СИЛА ", label), (str(p.strength), attr(Color.RED, curses.A_BOLD)), (" |", label),
        ("   ЛОВК ", label), (str(p.agility), attr(Color.CYAN, curses.A_BOLD)), (" |", label),
        ("   * ", gold), (str(p.backpack.treasure), gold), (" |", label),
    ] + keys + [
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



