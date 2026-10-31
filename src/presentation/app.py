"""Главный цикл: ввод -> команда -> события -> отрисовка."""
from __future__ import annotations

import curses

from domain import events as ev
from domain.balance import LEVEL_H, LEVEL_W
from domain.ports import SaveRepository
from domain.session import GameSession, GameState
from presentation import menus, screens
from presentation.input import OpenMenu, Quit, read_key, translate
from presentation.messages import format_event
from presentation.renderer import EXTRA_COLS, EXTRA_ROWS, draw, put
from presentation.theme import init_colors

MIN_ROWS = LEVEL_H + EXTRA_ROWS
MIN_COLS = LEVEL_W + EXTRA_COLS
MESSAGE_LIMIT = 6


def run(screen, repo: SaveRepository, new_game) -> None:
    """Главное меню. new_game - функция, которая создаёт новую игру."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    init_colors()

    while True:
        saved = repo.load_session()
        choice = menus.choose_main(screen, saved is not None)
        if choice == "new":
            play(screen, new_game(), repo)
        elif choice == "continue":
            play(screen, saved, repo)
        elif choice == "records":
            screens.show_records(screen, repo.top_records())
        else:
            return

def play(screen, session: GameSession, repo: SaveRepository) -> None:
    """Играет, пока игрок не выйдет в меню или игра не закончится."""
    messages: list[str] = []
    while True:
        if not _wait_for_big_enough_terminal(screen):
            break
        draw(screen, session, messages)

        request = translate(read_key(screen))
        if request is None:
            continue
        if isinstance(request, Quit):
            break
        if isinstance(request, OpenMenu):
            request = menus.choose_item(screen, session.player, request.item_type)
            if request is None:
                continue
        for event in session.handle(request):
            if isinstance(event, ev.LevelChanged):
                repo.save_session(session)
            text = format_event(event)
            if text:
                messages.append(text)
        messages = messages[-MESSAGE_LIMIT:]
        if session.state is not GameState.PLAYING:
            draw(screen, session, messages)
            screens.show_end(screen, session.state, session.stats)
            break

    finish(session, repo)


def finish(session: GameSession, repo: SaveRepository) -> None:
    """Что делать с игрой, когда мы её покинули: сохранить или записать результат."""
    if session.state is GameState.PLAYING:
        repo.save_session(session)      # вышли в меню: запоминаем, где остановились
    else:
        repo.add_record(session.stats)  # игра закончилась: результат в таблицу рекордов
        repo.delete_session()           # а сохранение больше не нужно

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
