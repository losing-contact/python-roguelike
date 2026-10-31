"""Экраны рекордов и результата прохождения."""
from __future__ import annotations

from domain.session import GameState
from domain.stats import RunStats
from presentation.input import read_key
from presentation.renderer import put
from presentation.theme import Color, attr

COLUMNS = [
    ("№", 3), ("Сокр.", 7), ("Ур.", 5), ("Враги", 7), ("Еда", 5),
    ("Эликс.", 8), ("Свитки", 8), ("Нанес.", 8), ("Получ.", 8), ("Шаги", 7),
]


def make_row(values):
    """Строка таблицы: каждое значение выровнено вправо по ширине своего столбца."""
    return "".join(f"{value:>{width}}" for value, (_, width) in zip(values, COLUMNS))


def show_records(screen, records) -> None:
    """Показывает лучшие прохождения и ждёт клавишу для возврата в меню."""
    rows, cols = screen.getmaxyx()
    left = max(0, (cols - sum(width for _, width in COLUMNS)) // 2)
    screen.erase()
    put(screen, 0, left, "РЕКОРДЫ")
    put(screen, 2, left, make_row(title for title, _ in COLUMNS))
    if not records:
        put(screen, 3, left, "Пока нет завершённых прохождений.")
    for index, stats in enumerate(records, start=1):
        if index + 2 >= rows - 2:
            break
        put(screen, index + 2, left, make_row([
            index, stats.treasure, stats.level_reached, stats.enemies_killed,
            stats.food_eaten, stats.elixirs_drunk, stats.scrolls_read,
            stats.hits_dealt, stats.hits_received, stats.steps,
        ]))
    put(screen, rows - 1, 0, "Нажмите любую клавишу для возврата в меню")
    screen.refresh()
    read_key(screen)


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


def show_end(screen, state: GameState, stats: RunStats) -> None:
    color = attr(Color.GREEN if state is GameState.WON else Color.RED)
    lines = build_lines(state, stats)
    rows, cols = screen.getmaxyx()
    screen.erase()
    for i, line in enumerate(lines):
        put(screen, rows // 2 - len(lines) // 2 + i, max(0, (cols - len(line)) // 2),
            line, color if i == 0 else 0)
    screen.refresh()
    read_key(screen)
