from presentation.input import read_key
from presentation.renderer import put


COLUMNS = [
    ("№", 3), ("Сокр.", 7), ("Ур.", 5), ("Враги", 7), ("Еда", 5),
    ("Эликс.", 8), ("Свитки", 8), ("Удары", 8), ("Промах", 8), ("Шаги", 7),
]


def make_row(values):
    """Строка таблицы: каждое значение выровнено вправо по ширине своего столбца."""
    return "".join(f"{value:>{width}}" for value, (_, width) in zip(values, COLUMNS))


def show(screen, records) -> None:
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
            stats.hits_dealt, stats.hits_missed, stats.steps,
        ]))
    put(screen, rows - 1, 0, "Нажмите любую клавишу для возврата в меню")
    screen.refresh()
    read_key(screen)
