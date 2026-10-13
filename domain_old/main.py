import curses
from logic import Game
from map import load_map, load_items
from generator import generate_all
import view

LEVELS = 5

def main():
    generate_all(LEVELS)
    game = Game(load_map, load_items)
    curses.wrapper(view.run, game)

if __name__ == "__main__":
    main()