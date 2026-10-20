#точка входа 


from __future__ import annotations 

import argparse 
import random
import sys
from pathlib import Path


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

    from datalayer.json_repository import JsonRepository
    from domain.session import GameSession
    from presentation import app

    repo = JsonRepository(Path(__file__).parent / "saves")
    curses.wrapper(app.run, repo, lambda: GameSession(random.Random(args.seed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())