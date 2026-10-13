"""Точка входа и единственное место, где слои собираются вместе (composition root).

Запуск из папки src:  python3 main.py [--seed N]
"""
from __future__ import annotations

import argparse
import random
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rogue на Python и curses")
    parser.add_argument("--seed", type=int, default=None,
                        help="зерно генератора: с тем же числом получится тот же мир")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
