"""Главный цикл: ввод -> команда -> события -> отрисовка."""
from __future__ import annotations

import curses
from domain.ports import SaveRepository

from domain import events as ev
from domain.balance import LEVEL_H, LEVEL_W
from domain.session import GameSession, GameState
from presentation import end_screen, menus
from presentation.colors import init_colors
from presentation.input import OpenMenu, Quit, read_key, translate
from presentation.messages import format_event
from presentation.renderer import draw, put

MIN_ROWS = LEVEL_H + 3     # карта + статус + сообщения + подсказка
MIN_COLS = LEVEL_W
MESSAGE_LIMIT = 6


def run(screen, session: GameSession, repo: SaveRepository) -> None:   # новый параметр

    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    init_colors()

    messages: list[str] = []
    while True:
        if not _wait_for_big_enough_terminal(screen):
            return
        draw(screen, session, messages)

        request = translate(read_key(screen))
        if request is None:
            continue
        if isinstance(request, Quit):
            return
        if isinstance(request, OpenMenu):
            command = menus.choose_item(screen, session.player, request.item_type)
            if command is None:
                continue
        else:
            command = request

        events = session.handle(command)
        messages.extend(text for e in events if (text := format_event(e)))
        del messages[:-MESSAGE_LIMIT]

        if session.state is not GameState.PLAYING:
            draw(screen, session, messages)
            end_screen.show(screen, session.state, session.stats)
            return

    del messages[:-MESSAGE_LIMIT]

    if any(isinstance(e, ev.LevelChanged) for e in events):  # после этой строки
        repo.save_session(session)

def _wait_for_big_enough_terminal(screen) -> bool:
    """Пока окно мало - просим увеличить, а не падаем с curses.error. False - игрок вышел."""
    while True:
        rows, cols = screen.getmaxyx()
        if rows >= MIN_ROWS and cols >= MIN_COLS:
            return True
        screen.erase()
        put(screen, 0, 0, f"Окно {cols}x{rows}, нужно минимум {MIN_COLS}x{MIN_ROWS}.")
        put(screen, 1, 0, "Увеличьте окно (q - выход).")
        screen.refresh()
        key = read_key(screen)
        if isinstance(key, str) and key.lower() in ("q", "й"):
            return False
