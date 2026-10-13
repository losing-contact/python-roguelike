import curses
import end_screen

KEYS = {
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
}

FRAME_COLOR = 2  # пара цветов, можно завести отдельную

def draw_frame(screen, h, w):
    screen.addstr(0, 0, '╔' + '═' * w + '╗', curses.color_pair(FRAME_COLOR))
    for y in range(1, h + 1):
        screen.addstr(y, 0, '║', curses.color_pair(FRAME_COLOR))
        screen.addstr(y, w + 1, '║', curses.color_pair(FRAME_COLOR))
    screen.addstr(h + 1, 0, '╚' + '═' * w + '╝', curses.color_pair(FRAME_COLOR))



def draw(screen, game):
    screen.clear()
    h = len(game.tiles)
    w = len(game.tiles[0])

    draw_frame(screen, h, w)
    p = game.player
    screen.addstr(h + 2, 0, f"[{'█' * p.health_blocks:<{p.max_blocks}}]")  # вместо Player.health
    screen.addstr(h + 3, 0, "↑ ↓ ← → Q   E - инвентарь")
    if game.pending_item:
        screen.addstr(h + 4, 0, f"Поднять «{game.pending_item.name}»? (y/n)")

    if DEBUG:
        draw_debug(screen, game, w)      # было: draw_debug(screen, game, h + 7)

    for y, row in enumerate(game.tiles):
        for x, tile in enumerate(row):
            if (x, y) == (game.player.x, game.player.y):
                screen.addch(y + 1, x + 1, '█')
            elif tile == '0':
                screen.addch(y + 1, x + 1, '█', curses.color_pair(1))
            elif tile == 'X':
                screen.addch(y + 1, x + 1, 'X', curses.color_pair(1))
            elif tile == 'F':
                screen.addch(y + 1, x + 1, 'F', curses.color_pair(3))
            elif tile == 'Z':
                screen.addch(y + 1, x + 1, 'Z', curses.color_pair(3))
            elif tile == 'V':
                screen.addch(y + 1, x + 1, 'V', curses.color_pair(3))
            else:
                screen.addch(y + 1, x + 1, ' ')

    for (x, y), item in game.items.items():
        if (x, y) != (game.player.x, game.player.y):
            screen.addch(y + 1, x + 1, 'i', curses.color_pair(4))

    for e in game.enemies:
        screen.addch(e.y + 1, e.x + 1, e.symbol, curses.color_pair(e.color))

    screen.refresh()

def run(screen, game):
    curses.start_color()
    curses.init_pair(1, 102, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    screen.keypad(True)
    curses.curs_set(0)

    while True:
        draw(screen, game)
        if game.result is not None:
            break
        key = screen.getch()

        if game.pending_item:
            if key == ord('y'):
                game.pick_up()
            elif key == ord('n'):
                game.decline()
        elif key in KEYS:
            game.move_player(*KEYS[key])
        elif key == ord('e'):
            show_inventory(screen, game)
        elif key == ord('q'):
            break

        if game.result is not None:
            end_screen.show(screen, game.result)
    return game


DEBUG = True

def draw_debug(screen, game, w):
    rows, cols = screen.getmaxyx()
    x = w + 4                                  # правее рамки карты
    p = game.player
    lines = [f"{p.name:<8} hp {p.health}/{p.max_health}  agi {p.agility}  str {p.strength}  ({p.x},{p.y})"]
    lines += game.log                          # события боя сразу под игроком
    lines.append("")
    lines += [f"{e.name:<8} hp {e.health}/{e.max_health}  agi {e.agility}  str {e.strength}  ({e.x},{e.y})"
              for e in game.enemies]
    for i, line in enumerate(lines):
        if i < rows - 1 and x < cols - 1:
            screen.addstr(i, x, line[:cols - x - 1])


def show_inventory(screen, game):
    names = [i.name for i in game.player.inventory] or ["(пусто)"]
    lines = ["Инвентарь", ""] + names
    h, w = screen.getmaxyx()
    curses.flushinp()
    screen.clear()
    for i, line in enumerate(lines):
        y = h // 2 - len(lines) // 2 + i
        x = max(0, (w - len(line)) // 2)
        screen.addstr(y, x, line)
    screen.refresh()
    screen.getch()