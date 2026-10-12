from dataclasses import replace

from domain import events as ev
from domain.commands import Move, UseItem
from domain.enemies.factory import create_enemy
from domain.enemies.types import EnemyKind
from domain.models.items import Item, ItemType
from domain.models.position import Pos
from domain.session import GameState

ROOM = [
    "#########",
    "#.......#",
    "#.@.....#",
    "#.......#",
    "#########",
]

CORRIDOR_AND_EXIT = [
    "######",
    "#@..>#",
    "######",
]

RIGHT, LEFT, UP, DOWN = Move(1, 0), Move(-1, 0), Move(0, -1), Move(0, 1)


def put_enemy(session, kind, x, y):
    enemy = create_enemy(kind, Pos(x, y), 1)
    session.level.enemies.append(enemy)
    return enemy


def put_item(session, x, y, **kw):
    item = Item(**kw)
    session.level.items[Pos(x, y)] = item
    return item


# --- движение ---------------------------------------------------------------
def test_player_starts_on_level_start(make_session):
    s = make_session([ROOM])
    assert s.player.pos == s.level.start == Pos(2, 2)


def test_move_changes_position_and_counts_steps(make_session):
    s = make_session([ROOM])
    events = s.handle(RIGHT)
    assert s.player.pos == Pos(3, 2)
    assert any(isinstance(e, ev.Moved) for e in events)
    assert s.stats.steps == 1


def test_wall_bump_does_not_spend_turn(make_session):
    s = make_session([ROOM])
    z = put_enemy(s, EnemyKind.ZOMBIE, 7, 3)
    s.player.pos = Pos(1, 1)
    assert s.handle(UP) == []
    assert s.handle(LEFT) == []
    assert z.timer == 0                      # враги не ходили


def test_move_spends_turn_and_enemies_act(make_session):
    s = make_session([ROOM])
    z = put_enemy(s, EnemyKind.ZOMBIE, 7, 3)
    s.handle(RIGHT)
    assert z.timer == 1


# --- бой --------------------------------------------------------------------
def test_moving_into_enemy_attacks_it(make_session, hit_rng):
    s = make_session([ROOM], hit_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 3, 2)
    z.health = 5
    events = s.handle(RIGHT)
    assert s.player.pos == Pos(2, 2)         # на месте атаки не двигаемся
    assert any(isinstance(e, ev.PlayerAttacked) and e.hit for e in events)
    assert z not in s.level.enemies


def test_killing_enemy_gives_treasure(make_session, hit_rng):
    s = make_session([ROOM], hit_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 3, 2)
    z.health = 1
    events = s.handle(RIGHT)
    killed = next(e for e in events if isinstance(e, ev.EnemyKilled))
    assert killed.treasure >= 1
    assert s.player.backpack.treasure == killed.treasure == s.stats.treasure
    assert s.stats.enemies_killed == 1


def test_stats_count_hits_and_misses(make_session, miss_rng):
    s = make_session([ROOM], miss_rng)
    put_enemy(s, EnemyKind.ZOMBIE, 3, 2)
    s.handle(RIGHT)
    assert s.stats.hits_missed == 1 and s.stats.hits_dealt == 0


def test_adjacent_enemy_attacks_player(make_session, hit_rng):
    s = make_session([ROOM], hit_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 4, 2)
    z.spec = replace(z.spec, move_every=1)
    s.player.pos = Pos(2, 2)
    events = s.handle(RIGHT)                 # шаг в (3, 2): теперь враг в соседней клетке
    assert s.player.pos == Pos(3, 2)
    attack = next(e for e in events if isinstance(e, ev.EnemyAttacked))
    assert attack.hit and attack.damage == z.strength
    assert s.player.health == s.player.max_health - z.strength


def test_enemy_approaches_player_who_is_not_adjacent(make_session, miss_rng):
    s = make_session([ROOM], miss_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 5, 2)
    z.spec = replace(z.spec, move_every=1)
    events = s.handle(LEFT)                  # игрок в (1, 2), зомби в (5, 2)
    assert z.pos == Pos(4, 2)
    assert not any(isinstance(e, ev.EnemyAttacked) for e in events)


def test_enemy_acts_only_every_n_turns(make_session, miss_rng):
    s = make_session([ROOM], miss_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 7, 1)
    z.spec = replace(z.spec, move_every=2, hostility=20)
    before = z.pos
    s.handle(LEFT)
    assert z.pos == before                   # первый ход - пропуск
    s.handle(RIGHT)
    assert z.pos != before                   # второй - шаг


def test_player_death_ends_game(make_session, hit_rng):
    s = make_session([ROOM], hit_rng)
    v = put_enemy(s, EnemyKind.VAMPIRE, 4, 2)
    v.strength = 1000
    events = s.handle(RIGHT)                 # игрок шагает вплотную к вампиру, тот бьёт
    assert s.state is GameState.LOST
    assert s.player.health == 0
    assert any(isinstance(e, ev.PlayerDied) for e in events)
    assert s.handle(RIGHT) == []             # после смерти команды игнорируются


# --- преследование ----------------------------------------------------------
WALLED = [
    "###########",
    "#@...#....#",
    "#....#....#",
    "#....+....#",
    "###########",
]


def test_enemy_chases_along_shortest_path_around_walls(make_session, miss_rng):
    s = make_session([WALLED], miss_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 8, 1)
    z.spec = replace(z.spec, move_every=1, hostility=20)
    visited = []
    for i in range(10):                      # игрок ходит туда-сюда в левой комнате
        s.handle(RIGHT if i % 2 == 0 else LEFT)
        visited.append(z.pos)
    assert Pos(5, 1) not in visited and Pos(5, 2) not in visited   # сквозь стену не ходит
    assert Pos(5, 3) in visited                                    # идёт через проём


def test_pursuit_radius_is_enemy_hostility(make_session, miss_rng, monkeypatch):
    import domain.session as session_module

    seen = []
    real = session_module.bfs_path

    def spy(start, goal, passable, max_dist=None):
        seen.append(max_dist)
        return real(start, goal, passable, max_dist)

    monkeypatch.setattr(session_module, "bfs_path", spy)
    s = make_session([ROOM], miss_rng)
    z = put_enemy(s, EnemyKind.VAMPIRE, 7, 3)
    z.spec = replace(z.spec, move_every=1)
    s.handle(RIGHT)
    assert seen == [z.spec.hostility]


def test_enemy_without_path_wanders_inside_its_room(make_session, miss_rng):
    closed = [
        "#######",
        "#@#...#",
        "###...#",
        "#######",
    ]
    s = make_session([closed], miss_rng)
    z = put_enemy(s, EnemyKind.ZOMBIE, 4, 1)
    z.spec = replace(z.spec, move_every=1, hostility=20)
    for _ in range(30):                      # игрок отрезан стеной: пути нет, враг блуждает
        s._enemy_turn(z, [])
        assert s.level.tile_at(z.pos).value == "floor"
        assert z.pos.x >= 3


# --- предметы ---------------------------------------------------------------
def test_items_are_picked_up_automatically(make_session):
    s = make_session([ROOM])
    put_item(s, 3, 2, item_type=ItemType.FOOD, subtype="Яблоко", health=20)
    events = s.handle(RIGHT)
    assert any(isinstance(e, ev.ItemPickedUp) for e in events)
    assert len(s.player.backpack.items_of(ItemType.FOOD)) == 1
    assert Pos(3, 2) not in s.level.items


def test_full_backpack_leaves_item_on_floor(make_session):
    s = make_session([ROOM])
    for _ in range(9):
        s.player.backpack.add(Item(ItemType.FOOD, "Яблоко", health=1))
    put_item(s, 3, 2, item_type=ItemType.FOOD, subtype="Яблоко", health=20)
    events = s.handle(RIGHT)
    assert any(isinstance(e, ev.BackpackFull) for e in events)
    assert Pos(3, 2) in s.level.items


def test_food_heals_and_is_consumed(make_session):
    s = make_session([ROOM])
    s.player.health = 50
    s.player.backpack.add(Item(ItemType.FOOD, "Яблоко", health=20))
    events = s.handle(UseItem(ItemType.FOOD, 0))
    assert s.player.health == 70
    assert s.player.backpack.items_of(ItemType.FOOD) == []
    assert any(isinstance(e, ev.ItemUsed) for e in events)
    assert s.stats.food_eaten == 1


def test_invalid_slot_does_not_spend_turn(make_session):
    s = make_session([ROOM])
    z = put_enemy(s, EnemyKind.ZOMBIE, 7, 3)
    assert s.handle(UseItem(ItemType.FOOD, 3)) == []
    assert z.timer == 0


def test_scroll_is_permanent(make_session):
    s = make_session([ROOM])
    base = s.player.strength
    s.player.backpack.add(Item(ItemType.SCROLL, "Свиток силы", strength=7))
    s.handle(UseItem(ItemType.SCROLL, 0))
    for _ in range(100):
        s.handle(Move(0, 0))
    assert s.player.strength == base + 7
    assert s.stats.scrolls_read == 1


def test_elixir_wears_off(make_session):
    s = make_session([ROOM])
    base = s.player.strength
    s.player.backpack.add(Item(ItemType.ELIXIR, "Эликсир силы", strength=10, duration=2))
    s.handle(UseItem(ItemType.ELIXIR, 0))
    assert s.player.strength == base + 10
    events = s.handle(RIGHT)
    assert s.player.strength == base
    assert any(isinstance(e, ev.EffectExpired) for e in events)
    assert s.stats.elixirs_drunk == 1


# --- оружие -----------------------------------------------------------------
def sword(power=10, name="Меч"):
    return Item(ItemType.WEAPON, name, strength=power)


def test_equip_weapon_removes_it_from_backpack(make_session):
    s = make_session([ROOM])
    s.player.backpack.add(sword())
    s.handle(UseItem(ItemType.WEAPON, 0))
    assert s.player.weapon is not None
    assert s.player.backpack.items_of(ItemType.WEAPON) == []


def test_swapping_weapon_drops_old_one_on_neighbor_cell(make_session):
    s = make_session([ROOM])
    old = sword(5, "Кинжал")
    s.player.weapon = old
    s.player.backpack.add(sword(15, "Топор"))
    events = s.handle(UseItem(ItemType.WEAPON, 0))
    assert s.player.weapon.subtype == "Топор"
    dropped = [p for p, item in s.level.items.items() if item is old]
    assert len(dropped) == 1
    assert dropped[0].manhattan(s.player.pos) == 1
    assert any(isinstance(e, ev.WeaponDropped) for e in events)


def test_unequip_keeps_weapon_in_backpack(make_session):
    s = make_session([ROOM])
    s.player.weapon = sword()
    s.handle(UseItem(ItemType.WEAPON, None))
    assert s.player.weapon is None
    assert len(s.player.backpack.items_of(ItemType.WEAPON)) == 1


def test_unequip_with_empty_hands_is_noop(make_session):
    s = make_session([ROOM])
    assert s.handle(UseItem(ItemType.WEAPON, None)) == []


# --- уровни -----------------------------------------------------------------
def test_exit_moves_to_next_level(make_session):
    s = make_session([CORRIDOR_AND_EXIT, ROOM])
    s.handle(RIGHT)
    events = s.handle(RIGHT)
    assert s.level.number == 1               # ещё не дошли
    events = s.handle(RIGHT)
    assert s.level.number == 2
    assert any(isinstance(e, ev.LevelChanged) and e.level == 2 for e in events)
    assert s.player.pos == s.level.start
    assert s.stats.level_reached == 2


def test_leaving_last_level_wins(make_session):
    s = make_session([CORRIDOR_AND_EXIT])
    for _ in range(3):
        events = s.handle(RIGHT)
    assert s.state is GameState.WON
    assert any(isinstance(e, ev.GameWon) for e in events)
    assert s.handle(LEFT) == []


def test_character_state_survives_level_change(make_session):
    s = make_session([CORRIDOR_AND_EXIT, ROOM])
    s.player.backpack.treasure = 42
    s.player.strength += 5
    for _ in range(3):
        s.handle(RIGHT)
    assert s.player.backpack.treasure == 42
    assert s.player.strength == 25
