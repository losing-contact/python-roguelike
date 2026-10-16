"""Точка входа и единственное место, где слои собираются вместе (composition root).

Запуск из папки src:  python3 main.py [--seed N]
"""
from __future__ import annotations

import argparse
import random
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rogue на Python и curses")
    parser.add_argument("--continue", dest="resume", action="store_true",
                        help="продолжить сохранённую игру")
    args = parser.parse_args(argv)

    try:
        import curses
    except ImportError:
        print("Не найден модуль curses. На Windows выполните: pip install windows-curses")
        return 1

    from domain.session import GameSession
    from presentation import app

    session = GameSession(random.Random(args.seed))
    curses.wrapper(app.run, session)

    stats = session.stats
    print(f"Игра окончена: уровень {stats.level_reached}, сокровищ {stats.treasure}")
    from datalayer.json_repository import JsonRepository
    from domain.session import GameSession, GameState

    repo = JsonRepository(Path(__file__).parent / "saves")
    session = None
    if args.resume:
        session = repo.load_session()
        if session is None:
            print("Сохранения нет, начинаем новую игру")
    if session is None:
        session = GameSession(random.Random(args.seed))

    curses.wrapper(app.run, session, repo)

    if session.state is GameState.PLAYING:
        repo.save_session(session)  # вышли по q: запоминаем, где остановились
    else:
        repo.add_record(session.stats)  # игра закончилась: результат в таблицу рекордов
        repo.delete_session()  # и сохранение больше не нужно
    return 0


if __name__ == "__main__":
    sys.exit(main())
