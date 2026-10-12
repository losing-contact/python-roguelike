from __future__ import annotations

from domain.models.stats import RunStats
from domain.session import GameState
from presentation.colors import Color, attr
from presentation.input import read_key
from presentation.renderer import put


def build_lines(state: GameState, stats: RunStats) -> list[str]:
    title = "ПОБЕДА!" if state is GameState.WON else "ВЫ ПОГИБЛИ"
    return [
        title, "",
        f"Достигнут уровень: {stats.level_reached}",
        f"Сокровища: {stats.treasure}",
        f"Побеждено врагов: {stats.enemies_killed}",
        f"Съедено еды: {stats.food_eaten}",
        f"Выпито эликсиров: {stats.elixirs_drunk}",
        f"Прочитано свитков: {stats.scrolls_read}",
        f"Ударов нанесено / промахов: {stats.hits_dealt} / {stats.hits_missed}",
        f"Пройдено клеток: {stats.steps}",
        "", "Нажмите любую клавишу",
    ]


def show(screen, state: GameState, stats: RunStats) -> None:
    color = attr(Color.GREEN if state is GameState.WON else Color.RED)
    lines = build_lines(state, stats)
    rows, cols = screen.getmaxyx()
    screen.erase()
    for i, line in enumerate(lines):
        put(screen, rows // 2 - len(lines) // 2 + i, max(0, (cols - len(line)) // 2),
            line, color if i == 0 else 0)
    screen.refresh()
    read_key(screen)
