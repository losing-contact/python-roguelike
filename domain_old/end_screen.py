import curses

WIN = 1
LOSE = 0

def build(result):
    text = "WIN" if result == WIN else "LOSER"
    n = len(text) + 4
    return [
        "╔" + "═" * n + "╗",
        "║  " + text + "  ║",
        "╚" + "═" * n + "╝",
        "",
    ]

def show(screen, result):
    color = curses.color_pair(3 if result == WIN else 2)  # зелёный / красный
    lines = build(result)
    h, w = screen.getmaxyx()
    curses.flushinp()
    screen.clear()
    for i, line in enumerate(lines):
        y = h // 2 - len(lines) // 2 + i
        x = max(0, (w - len(line)) // 2)
        screen.addstr(y, x, line, color)
    screen.refresh()
    screen.getch()