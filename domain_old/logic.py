import random

SCALE = 10         # масштаб: 1 блок полоски здоровья = 10 единиц
GROWTH = 1.08      # множитель характеристик врагов за каждый уровень


class Entity:
    name = "Entity"
    max_health = 10 * SCALE
    agility = 3                    # ловкость
    strength = 1 * SCALE           # сила
    weapon = 0                     # модификатор оружия (тоже в единицах ×10)

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.health = self.max_health

    @property
    def alive(self):
        return self.health > 0

    @property
    def health_blocks(self):       # для отрисовки, минимум 1 блок пока жив
        return -(-self.health // SCALE)

    @property
    def max_blocks(self):
        return self.max_health // SCALE


class Player(Entity):
    name = "Player"
    max_health = 10 * SCALE        # 100
    agility = 3
    strength = 2 * SCALE           # 20

    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.inventory = []

    @property
    def treasure(self):
        return sum(i.cost for i in self.inventory if isinstance(i, Treasure))


class Enemy(Entity):
    symbol = '?'
    color = 3
    radius = 6        # радиус враждебности
    move_every = 2    # действует раз в N кадров
    loot = 5          # базовая ценность сокровищ с врага

    def __init__(self, x=0, y=0, level=1):
        super().__init__(x, y)
        self.timer = 0
        self.level = level
        k = GROWTH ** (level - 1)
        self.max_health = round(self.max_health * k)
        self.health = self.max_health
        self.strength = round(self.strength * k)
        self.agility += (level - 1) // 3   # ловкость растёт медленно


class Zombie(Enemy):
    name = "Zombie"
    symbol = 'Z'
    color = 3
    max_health = 5 * SCALE         # 50
    agility = 2
    strength = 1 * SCALE           # 10
    radius = 6
    move_every = 2
    loot = 5


class Vampire(Enemy):
    name = "Vampire"
    symbol = 'V'
    color = 2
    max_health = 8 * SCALE         # 80
    agility = 5
    strength = 2 * SCALE           # 20
    radius = 8
    move_every = 4
    loot = 10


ENEMY_TYPES = {'Z': Zombie, 'V': Vampire}


class Item:
    def __init__(self, name, cost=0):
        self.name = name
        self.cost = cost


class Treasure(Item):
    pass


class Heal(Item):
    pass


ITEM_TYPES = {'treasures': Treasure, 'heal': Heal}


def make_item(data):
    return ITEM_TYPES[data['class']](data['name'], int(data['cost']))


def hit_chance(attacker, target):
    chance = 0.6 + 0.05 * (attacker.agility - target.agility)
    return min(0.95, max(0.1, chance))


def attack(attacker, target):
    # Возвращает нанесённый урон, 0 - промах
    # 1. попадание
    if random.random() > hit_chance(attacker, target):
        return 0
    # 2. расчёт урона
    damage = attacker.strength + attacker.weapon
    # 3. применение урона
    target.health = max(0, target.health - damage)  # max нужен чтобы не уходило в минус
    return damage


class Game:
    def __init__(self, load_level, load_items):
        self.load_level = load_level
        self.load_items = load_items
        self.level = 1
        self.result = None            # None - идёт игра, 1 - победа, 0 - поражение
        self.log = []
        self.pending_item = None      # предмет, о котором ждём ответ y/n
        self.player = Player()
        self._setup(load_level(self.level), load_items(self.level))

    def _setup(self, tiles, items_data):
        self.tiles = tiles
        self.enemies = []
        self.items = {}               # {(x, y): Item}
        n = 0
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile in ENEMY_TYPES:
                    self.enemies.append(ENEMY_TYPES[tile](x, y, self.level))
                    tiles[y][x] = '1'  # под врагом обычный пол
                elif tile == 'i':
                    if n >= len(items_data):
                        raise ValueError(f"на уровне {self.level} больше 'i', чем предметов в файле")
                    self.items[(x, y)] = make_item(items_data[n])
                    n += 1
                    tiles[y][x] = '1'
        self.player.x, self.player.y = self.find('S')

    def find(self, char):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if tile == char:
                    return x, y
        raise ValueError(f"на уровне {self.level} нет клетки '{char}'")

    def next_level(self):
        tiles = self.load_level(self.level + 1)
        if tiles is None:
            return
        self.level += 1
        self._setup(tiles, self.load_items(self.level))

    def is_walkable(self, x, y):
        return (0 <= y < len(self.tiles)
                and 0 <= x < len(self.tiles[y])
                and self.tiles[y][x] != '0')

    def enemy_at(self, x, y):
        for e in self.enemies:
            if e.x == x and e.y == y:
                return e
        return None

    def _fight(self, attacker, target):
        dmg = attack(attacker, target)
        if dmg:
            self.log.append(f"{attacker.name} -> {target.name}: -{dmg}")
        else:
            self.log.append(f"{attacker.name} -> {target.name}: промах")
        if not target.alive:
            self.log.append(f"{target.name} погиб")
            if isinstance(target, Enemy):
                value = target.loot * self.level
                self.player.inventory.append(Treasure("Сокровища", value))
                self.log.append(f"+{value} сокровищ")
        self.log = self.log[-4:]

    def move_player(self, dx, dy):
        if self.pending_item:
            return
        nx, ny = self.player.x + dx, self.player.y + dy
        target = self.enemy_at(nx, ny)
        if target:
            self._fight(self.player, target)      # движение в сторону врага = атака
        elif self.is_walkable(nx, ny):
            self.player.x, self.player.y = nx, ny
            tile = self.tiles[ny][nx]
            if tile == 'F':
                self.result = 1
                return
            if tile == 'X':
                self.next_level()
                return
            if (nx, ny) in self.items:
                self.pending_item = self.items[(nx, ny)]
        self._tick()

    def _tick(self):
        self.enemies = [e for e in self.enemies if e.alive]
        for e in self.enemies:
            dist = abs(e.x - self.player.x) + abs(e.y - self.player.y)
            if dist <= e.radius:
                e.timer += 1
                if e.timer >= e.move_every:
                    e.timer = 0
                    self._move_enemy(e)
            else:
                e.timer = 0
            if not self.player.alive:
                self.result = 0
                break

    def _move_enemy(self, e):
        px, py = self.player.x, self.player.y
        dx = (px > e.x) - (px < e.x)
        dy = (py > e.y) - (py < e.y)
        if abs(px - e.x) >= abs(py - e.y):
            options = [(dx, 0), (0, dy)]
        else:
            options = [(0, dy), (dx, 0)]
        for ox, oy in options:
            if (ox, oy) == (0, 0):
                continue
            nx, ny = e.x + ox, e.y + oy
            if (nx, ny) == (px, py):
                self._fight(e, self.player)       # шаг в сторону игрока = атака
                break
            if self.is_walkable(nx, ny) and not self.enemy_at(nx, ny):
                e.x, e.y = nx, ny
                break

    def pick_up(self):
        item = self.pending_item
        if item is None:
            return
        del self.items[(self.player.x, self.player.y)]
        self.player.inventory.append(item)
        self.pending_item = None

    def decline(self):
        self.pending_item = None