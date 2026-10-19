# Как добавить нового врага

Методичка по проекту `python-roguelike` (папка `src`). Сначала краткий итог по привидению,
потом пошаговая инструкция с готовыми шаблонами: копируете блок, подставляете свои значения
вместо `<...>`.

---

## 1. Что сделано для привидения

Привидение: белый `g`, высокая ловкость, низкие здоровье, сила и враждебность. Прыгает по комнате
и периодически становится невидимым, пока игрок не вступил в бой.

| Файл | Что добавлено |
|---|---|
| `domain/balance.py` | `GHOST_CHANCE`, `GHOST_VISIBLE_TURNS`, `GHOST_INVISIBLE_TURNS` |
| `domain/enemies/types.py` | `EnemyKind.GHOST`, `Trait.INVISIBLE_PHASES`, запись `GHOST` в `SPECS` |
| `domain/enemies/behaviors.py` | функции `room_cells` и `teleport`, запись в `PATTERNS` |
| `domain/enemies/invisibility.py` (новый) | функция `tick`: включает и выключает невидимость |
| `domain/models/entities.py` | поля `invisible` и `phase_turns` в классе `Enemy` |
| `domain/session.py` | `import invisibility` и вызов `invisibility.tick(...)` в `_end_of_turn` |
| `domain/enemies/factory.py` | шанс появления `GHOST_CHANCE` в `pick_enemy_kind` |
| `presentation/renderer.py` | невидимых врагов не рисуем: `and not enemy.invisible` |
| `presentation/theme.py` | символ `g`, белый, жирный |

Названия врагов в сообщениях (`messages.py`) подтягиваются из `SPECS` сами, там менять ничего не нужно.

---

## 2. Как враг живёт за один ход

После каждого хода игрока `session._end_of_turn` обходит всех врагов:

```
для каждого врага:
    invisibility.tick(...)              только для тех, у кого есть своё состояние
    _enemy_turn:
        1. счётчик timer < move_every   -> враг пропускает ход
        2. игрок рядом (1 клетка)       -> атака: combat.resolve_attack
        3. игрок ближе hostility        -> шаг по кратчайшему пути к игроку
        4. иначе                        -> PATTERNS[kind]  (как враг бродит)
```

Особенности (`Trait`) читает бой: `combat.py` проверяет `Trait.X in attacker.traits` / `target.traits`.

---

## 3. Что менять под нужную особенность

| Хочу | Механизм | Где |
|---|---|---|
| Просто другие числа (здоровье, сила, ловкость...) | поля в `SPECS` | `types.py` |
| Особое движение, когда игрока рядом нет | функция в `PATTERNS` | `behaviors.py` |
| Особенность в бою (промах, вытягивание, двойной удар) | `Trait` + проверка в бою | `types.py`, `combat.py` |
| Состояние, которое меняется по ходам (невидимость, сон, отдых) | поля в `Enemy` + модуль + вызов в сессии | `entities.py`, `enemies/<модуль>.py`, `session.py` |
| Враг не отображается в какие-то моменты | условие при отрисовке | `renderer.py` |
| Внешний вид | `Glyph` | `theme.py` |
| Как часто встречается | константа + порог | `balance.py`, `factory.py` |

---

## 4. Обязательные шаги (любой новый враг)

Заранее придумайте значения и запомните их, они подставляются во все шаги:

| Обозначение | Что это | Пример |
|---|---|---|
| `<NAME>` | имя в перечислении, ЗАГЛАВНЫМИ | `OGRE` |
| `<name>` | строка-значение, строчными | `ogre` |
| `<Название>` | как называется в игре | `Огр` |
| `<символ>` | буква на карте | `O` |
| `<ЦВЕТ>` | `WALL`, `RED`, `GREEN`, `YELLOW`, `CYAN`, `MAGENTA` | `YELLOW` |

### Шаг 1. `domain/balance.py`: шанс появления

Добавьте в конец файла:

```python
<NAME>_CHANCE = 0.10
```

### Шаг 2. `domain/enemies/types.py`: тип и характеристики

В класс `EnemyKind` добавьте строку:

```python
    <NAME> = "<name>"
```

В словарь `SPECS`, перед закрывающей `}`:

```python
    EnemyKind.<NAME>: EnemySpec(
        EnemyKind.<NAME>, "<Название>",
        max_health=5 * SCALE, agility=3, strength=1 * SCALE,
        hostility=6, move_every=1,
        traits=frozenset(),
    ),
```

Если у врага будет особенность, впишите её в `traits=frozenset({Trait.<TRAIT>})` (раздел 5).

### Шаг 3. `domain/enemies/behaviors.py`: как он ходит

Каждый враг обязан быть в `PATTERNS`, иначе в игре будет `KeyError`. Если особого движения нет,
используйте обычное:

```python
PATTERNS: dict[EnemyKind, Pattern] = {
    EnemyKind.ZOMBIE: random_walk,
    EnemyKind.VAMPIRE: random_walk,
    EnemyKind.<NAME>: random_walk,
}
```

### Шаг 4. `domain/enemies/factory.py`: когда он появляется

В импорт из `domain.balance` добавьте `<NAME>_CHANCE`. В конце `pick_enemy_kind`, перед
`return EnemyKind.ZOMBIE`, добавьте блок:

```python
    if roll < vampire_chance + GHOST_CHANCE + <NAME>_CHANCE:
        return EnemyKind.<NAME>
```

Если ваш враг не первый после привидения, порог каждого следующего блока включает все предыдущие
шансы. Сумма всех шансов должна быть меньше 1, иначе зомби перестанут появляться:

```python
    roll = rng.random()
    if roll < vampire_chance:
        return EnemyKind.VAMPIRE
    if roll < vampire_chance + GHOST_CHANCE:
        return EnemyKind.GHOST
    if roll < vampire_chance + GHOST_CHANCE + <NAME>_CHANCE:
        return EnemyKind.<NAME>
    return EnemyKind.ZOMBIE
```

### Шаг 5. `presentation/theme.py`: как выглядит

В словарь `ENEMY_GLYPHS`:

```python
    EnemyKind.<NAME>: Glyph("<символ>", Color.<ЦВЕТ>, curses.A_BOLD),
```

Третий параметр необязателен. Варианты: `curses.A_BOLD` (ярче), `curses.A_DIM` (тусклее).

### Шаг 6. Проверка

```bash
python3 -c "from domain.enemies.types import SPECS, EnemyKind; print(list(SPECS))"
python3 main.py --seed 1
```

Чтобы увидеть врага сразу, временно поставьте `<NAME>_CHANCE = 0.9` в `balance.py`
и верните значение назад.

---

## 5. Особенности (нужны не всем врагам)

### 5.1. Своё движение (`behaviors.py`)

Функция вызывается, когда игрока нет рядом. Она возвращает клетку, куда враг перейдёт, или `None`
(остаться на месте). Вставьте перед `PATTERNS`:

```python
def <имя_функции>(enemy: Enemy, level: Level, rng: random.Random) -> Pos | None:
    """<что делает>."""
    options = [p for p in enemy.pos.neighbors() if level.can_enemy_enter(p)]
    return rng.choice(options) if options else None
```

Подключение: в `PATTERNS` вместо `random_walk` поставьте `<имя_функции>`. Клетка может быть не
соседней: привидение так телепортируется. Полезные методы: `level.tile_at(pos)`,
`level.can_enemy_enter(pos)`, `pos.neighbors()`, `Tile.FLOOR` (пол комнаты).

### 5.2. Особенность в бою (`types.py` + `combat.py`)

1. В `Trait` (`types.py`) добавьте:

```python
    <TRAIT> = "<trait>"   # <что делает>
```

2. Впишите её в `traits=frozenset({Trait.<TRAIT>})` у врага в `SPECS`.
3. В `resolve_attack` (`combat.py`) добавьте проверку. Есть два типичных места.

Перед проверкой попадания (так сделан `FIRST_HIT_MISS`):

```python
    if Trait.<TRAIT> in target.traits and <условие>:
        return AttackResult(hit=False)
```

После нанесения урона (так сделан `DRAIN_MAX_HEALTH`, он стоит перед `return`):

```python
    if Trait.<TRAIT> in attacker.traits and target.alive:
        <действие над target>
```

Если игроку нужно показать сообщение об эффекте:

1. `combat.py`: добавьте поле в `AttackResult`;
2. `events.py`: добавьте то же поле в нужное событие (`PlayerAttacked` или `EnemyAttacked`);
3. `session.py`: передайте поле при создании события (в `_player_attack` или `_enemy_attack`);
4. `presentation/messages.py`: выведите текст в `format_event`.

Тексты для игрока пишутся только в `presentation`, не в `domain`.

### 5.3. Состояние по ходам (как у привидения)

Так делается всё, что меняется со временем: невидимость, сон, отдых после удара.

1. Поля в конец класса `Enemy` (`domain/models/entities.py`), обязательно со значениями по умолчанию:

```python
    <поле>: <тип> = <значение>
```

2. Новый файл `domain/enemies/<модуль>.py`:

```python
from __future__ import annotations

import random

from domain.enemies.types import Trait
from domain.models.entities import Enemy
from domain.models.position import Pos


def tick(enemy: Enemy, player_pos: Pos, rng: random.Random) -> None:
    """Вызывать каждый ход врага."""
    if Trait.<TRAIT> not in enemy.traits:
        return
    # логика: меняем поля enemy
```

3. Вызов в `domain/session.py`, в `_end_of_turn`, рядом с вызовом `invisibility.tick(...)`:

```python
from domain.enemies import <модуль>

            if enemy.alive:
                invisibility.tick(enemy, self.player.pos, self.rng)
                <модуль>.tick(enemy, self.player.pos, self.rng)
                self._enemy_turn(enemy, events)
```

Импорт идёт вверх файла, к остальным `import`. Функция сама проверяет `Trait`, поэтому
для остальных врагов она ничего не делает.

Названия модулей не должны совпадать с уже существующими: `domain/visibility.py`
(туман войны) уже есть.

### 5.4. Скрыть врага при отрисовке (`presentation/renderer.py`)

В цикле по врагам добавьте условие со своим полем:

```python
        if enemy.pos in session.visible and not enemy.<поле_скрытия>:
```

---

## 6. Как подобрать числа

Здоровье и сила считаются в «десятках»: `SCALE = 10`, то есть `5 * SCALE` это 50 здоровья
и 5 блоков полоски. У игрока: здоровье `10 * SCALE`, сила `2 * SCALE`, ловкость 3.

| Враг | Здоровье | Ловкость | Сила | Враждебность | `move_every` |
|---|---|---|---|---|---|
| Зомби | `5 * SCALE` | 2 | `1 * SCALE` | 6 | 2 |
| Вампир | `8 * SCALE` | 4 | `2 * SCALE` | 8 | 2 |
| Привидение | `2 * SCALE` | 8 | `SCALE // 2` | 3 | 1 |

- **Ловкость**: шанс попадания `0.6 + 0.05 * (ловкость атакующего - ловкость цели)`, от 10% до 95%.
  Ловкость 8 у врага против ловкости 3 у игрока: игрок попадает примерно в 35% ударов.
- **Враждебность**: с какого расстояния (в клетках) враг замечает игрока и идёт за ним по кратчайшему пути.
- **`move_every`**: враг действует раз в N ходов игрока. `1` значит каждый ход, `2` значит вдвое медленнее.
- **Рост по уровням**: здоровье и сила умножаются на `ENEMY_GROWTH ** (уровень - 1)`, ловкость растёт на 1 за 3 уровня.
  Задавайте числа для первого уровня, дальше они подрастут сами.

---

## 7. Частые ошибки

| Сообщение | Причина |
|---|---|
| `AttributeError: type object 'EnemyKind' has no attribute '<NAME>'` | не добавили пункт в `EnemyKind` (шаг 2) |
| `AttributeError: ... 'Trait' has no attribute` | не добавили особенность в `Trait` |
| `KeyError: <EnemyKind...>` в `session.py` | врага нет в `PATTERNS` (шаг 3) |
| Враг есть, но его не видно на карте | нет записи в `ENEMY_GLYPHS` (шаг 5) |
| Враг никогда не появляется | не добавлен порог в `pick_enemy_kind` (шаг 4) или шанс слишком мал |
| Зомби пропали | сумма шансов в `pick_enemy_kind` стала >= 1 |
| `ModuleNotFoundError` или `module has no attribute 'tick'` | опечатка в имени файла или файл неполный: `ls domain/enemies` |
| `NameError` в `behaviors.py` | функция паттерна стоит ниже `PATTERNS`, переместите выше |
| Поля состояния теряются после загрузки сохранения | они не добавлены в `datalayer/serializers.py` (`session_to_dict` и `session_from_dict`); игре это не мешает, но состояние сбрасывается |

---

## 8. Git и проверка перед merge request

```bash
git switch develop && git pull
git switch -c feat/<name>-enemy
# ... правки ...
make test lint
git add -A
git commit -m "feat: add <name> enemy"
git push -u origin feat/<name>-enemy
```

По `CONTRIBUTING.md` на новое поведение нужен тест, числа баланса лежат в `balance.py`,
тексты для игрока только в `presentation`, `domain` не импортирует `curses`.

### Чек-лист нового врага

- [ ] `balance.py`: константа шанса `<NAME>_CHANCE`
- [ ] `types.py`: пункт в `EnemyKind`, запись в `SPECS` (и `Trait`, если нужна особенность)
- [ ] `behaviors.py`: запись в `PATTERNS`
- [ ] `factory.py`: импорт константы и порог в `pick_enemy_kind`
- [ ] `theme.py`: запись в `ENEMY_GLYPHS`
- [ ] особенности: `combat.py` / модуль состояния / поля в `Enemy` / вызов в `session.py` (если нужны)
- [ ] `renderer.py`: условие скрытия (если враг бывает невидимым)
- [ ] игра запускается, враг появляется, ведёт себя как задумано
- [ ] тест написан, `make test lint` проходит