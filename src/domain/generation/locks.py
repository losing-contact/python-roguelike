"""Запертые двери и ключи к ним, как в DOOM.

Дверь стоит в проёме между комнатой и коридором и открывается ключом своего цвета.
Ключи не пропадают после использования и действуют до конца уровня.

Расставить ключи наугад нельзя: ключ может оказаться за собственной дверью, и уровень
невозможно пройти (софтлок). Поэтому ключи кладём только туда, куда игрок уже может дойти, а
готовый уровень проверяем ещё раз. И для этого, и для проверки нужен поиск в ширину, в котором
запертая дверь проходима только с ключом нужного цвета. Найденные ключи открывают новые двери,
поиск повторяется, пока находятся новые ключи.
"""
from domain.balance import LEVELS_PER_LOCK
from domain.geometry import bfs_distances
from domain.models.keys import KeyColor
from domain.models.tile import WALKABLE, Tile

ATTEMPTS = 20


def lock_count(level_number):
    """Сколько запертых дверей на уровне: на первом нет, дальше их всё больше."""
    return min(len(KeyColor), (level_number + 1) // LEVELS_PER_LOCK)


def place_locks(level, rng, count):
    """Запирает до count дверей и раскладывает ключи. Если ничего не вышло, без дверей.

    Сначала пробуем поставить все двери, а если не получается, на одну меньше, и так далее.
    """
    free = free_cells(level)
    for doors in range(count, 0, -1):
        for _ in range(ATTEMPTS):
            corridors = choose_corridors(level, rng, doors)
            if not corridors:
                break
            colors = rng.sample(list(KeyColor), len(corridors))
            level.doors = {}
            for corridor, color in zip(corridors, colors):
                level.doors[rng.choice([corridor.door_a, corridor.door_b])] = color
            level.keys = {}
            if place_keys(level, rng, colors, free) and not lock_problems(level):
                return
    level.doors = {}
    level.keys = {}


def place_keys(level, rng, colors, free):
    """Кладёт ключи по одному, каждый только туда, куда игрок уже может дойти.

    Поэтому ключ не окажется за своей дверью. False, если класть некуда.
    """
    for color in colors:
        seen, _ = collect_keys(level)
        cells = [cell for cell in free if cell in seen and cell not in level.keys]
        if not cells:
            return False
        level.keys[rng.choice(cells)] = color
    return True


def free_cells(level):
    """Клетки, куда можно положить ключ: не в стартовой комнате и не под врагом или предметом."""
    busy = {enemy.pos for enemy in level.enemies} | set(level.items) | {level.exit}
    return [cell for room in level.rooms if room.id != level.start_room
            for cell in room.cells() if cell not in busy]


def choose_corridors(level, rng, count):
    """Какие коридоры запереть. Только те, без которых комнаты распались бы на две части:
    запирать коридор, в обход которого можно пройти, бессмысленно."""
    bridges = [c for c in level.corridors if not rooms_connected(level, c, c.room_a, c.room_b)]
    if not bridges:
        return []
    # хотя бы одна дверь должна стоять на пути к выходу, иначе ключи не нужны
    on_the_way = [c for c in bridges
                  if not rooms_connected(level, c, level.start_room, level.exit_room)]
    first = rng.choice(on_the_way or bridges)
    others = [c for c in bridges if c is not first]
    return [first] + rng.sample(others, min(count - 1, len(others)))


def rooms_connected(level, skipped, start, goal):
    """Можно ли дойти из комнаты start в комнату goal по коридорам, кроме коридора skipped."""
    seen = {start}
    stack = [start]
    while stack:
        room = stack.pop()
        for corridor in level.corridors:
            if corridor is skipped:
                continue
            for here, there in ((corridor.room_a, corridor.room_b),
                                (corridor.room_b, corridor.room_a)):
                if here == room and there not in seen:
                    seen.add(there)
                    stack.append(there)
    return goal in seen


def can_pass(level, keys):
    """Функция «проходима ли клетка» для игрока, у которого есть ключи keys."""
    def passable(pos):
        if level.tile_at(pos) not in WALKABLE:
            return False
        color = level.doors.get(pos)
        return color is None or color in keys
    return passable


def collect_keys(level):
    """Поиск в ширину с ключами. Возвращает (клетки, до которых можно дойти, собранные ключи)."""
    keys = set()
    while True:
        seen = bfs_distances(level.start, can_pass(level, keys))
        found = {color for pos, color in level.keys.items() if pos in seen}
        if found <= keys:   # новых ключей нет: больше ничего не откроется
            return seen, keys
        keys |= found


def lock_problems(level):
    """Что не так с дверями и ключами. Пустой список: уровень можно пройти."""
    problems = []
    for pos in level.doors:
        if level.tile_at(pos) is not Tile.DOORWAY:
            problems.append(f"запертая дверь не в проёме: {pos}")

    start_room = level.rooms[level.start_room]
    for pos in level.keys:
        if level.tile_at(pos) is not Tile.FLOOR or start_room.contains(pos):
            problems.append(f"ключ лежит не там, где можно: {pos}")
        if pos in level.items or level.enemy_at(pos) is not None:
            problems.append(f"на клетке ключа что-то лежит или стоит: {pos}")

    seen, keys = collect_keys(level)
    if level.exit not in seen:
        problems.append("до выхода не дойти, даже собрав все достижимые ключи")
    for color in set(level.doors.values()):
        if color not in keys:
            problems.append(f"до ключа {color.value} не дойти")
    return problems
