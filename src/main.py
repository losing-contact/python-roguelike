"""Точка входа и единственное место, где слои собираются вместе (composition root).

Запуск из папки src:  python3 main.py [--seed N]
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rogue на Python и curses")
    parser.add_argument("--continue", dest="resume", action="store_true",
                        help="продолжить сохранённую игру")
    parser.add_argument("--seed", type=int, default=None,
                        help="сид генератора случайных чисел")
    args = parser.parse_args(argv)

    try:
        import curses
    except ImportError:
        print("Не найден модуль curses. На Windows выполните: pip install windows-curses")
        return 1

    from datalayer.json_repository import JsonRepository
    from domain.session import GameSession, GameState
    from presentation import app

    # Инициализируем репозиторий для сохранений
    repo = JsonRepository(Path(__file__).parent / "saves")

    session = None
    if args.resume:
        session = repo.load_session()
        if session is None:
            print("Сохранения нет, начинаем новую игру")

    # Если сохранения не было (или не запрашивали продолжение), создаем новую сессию
    if session is None:
        session = GameSession(random.Random(args.seed))

    # Запуск игры
    curses.wrapper(app.run, session, repo)

    # Сохранение или завершение игры в зависимости от статуса
    if session.state is GameState.PLAYING:
        repo.save_session(session)  # вышли по q: запоминаем, где остановились
        print("Игра сохранена.")
    else:
        stats = session.stats
        print(f"Игра окончена: уровень {stats.level_reached}, сокровищ {stats.treasure}")
        repo.add_record(stats)      # игра закончилась: результат в таблицу рекордов
        repo.delete_session()       # и сохранение больше не нужно

    return 0


if __name__ == "__main__":
    sys.exit(main())