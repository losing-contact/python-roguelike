# Rogue на Python (curses)

Консольный roguelike в духе Rogue 1980: 21 уровень, 9 комнат на уровень, пошаговый бой,
рюкзак, враги с разным поведением. Python 3.10, интерфейс на `curses`.

## Запуск

```bash
cd src
python3.10 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                      # на Windows поставит windows-curses
python3 main.py              # случайный мир
python3 main.py --seed 42    # воспроизводимый мир
```

Нужен терминал не меньше **78×24**. Если окно меньше, игра попросит его увеличить.

## Управление

| Клавиша | Действие |
|---|---|
| `W` `A` `S` `D` (или стрелки) | ход; шаг в сторону врага = атака |
| `h` / `j` / `k` / `e` | оружие / еда / эликсир / свиток: откроется список, выбор цифрами `1-9` (`0` у оружия - убрать из рук) |
| `q` | выход |

Работает и на русской раскладке (`ц ф ы в`, `р о л у`, `й`).

## Разработка

```bash
cd src
make test    # pytest
make lint    # ruff
```

- Архитектура, правила слоёв и «куда добавлять новое»: [`src/ARCHITECTURE.md`](src/ARCHITECTURE.md)
- Ветки, коммиты, merge request'ы: [`src/CONTRIBUTING.md`](src/CONTRIBUTING.md)
