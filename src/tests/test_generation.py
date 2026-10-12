import random

import pytest

from domain.balance import GRID_COLS, GRID_ROWS, LEVEL_H, LEVEL_W
from domain.generation.level_factory import generate_level
from domain.generation.populate import enemy_count, useful_count
from domain.generation.validate import find_problems
from domain.models.items import ItemType

SEEDS = range(25)
NUMBERS = (1, 8, 15, 21)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("number", NUMBERS)
def test_generated_level_is_valid(seed, number):
    level = generate_level(number, random.Random(seed))
    assert find_problems(level) == []


@pytest.mark.parametrize("seed", range(10))
def test_nine_rooms_one_per_section(seed):
    level = generate_level(1, random.Random(seed))
    assert len(level.rooms) == GRID_ROWS * GRID_COLS
    assert {(r.row, r.col) for r in level.rooms} == {
        (row, col) for row in range(GRID_ROWS) for col in range(GRID_COLS)
    }
    assert (level.width, level.height) == (LEVEL_W, LEVEL_H)


def test_same_seed_gives_same_level():
    a = generate_level(5, random.Random(42))
    b = generate_level(5, random.Random(42))
    assert a.tiles == b.tiles
    assert a.start == b.start and a.exit == b.exit
    assert [e.pos for e in a.enemies] == [e.pos for e in b.enemies]
    assert a.items == b.items


def test_different_seeds_give_different_levels():
    assert generate_level(5, random.Random(1)).tiles != generate_level(5, random.Random(2)).tiles


@pytest.mark.parametrize("number", NUMBERS)
def test_population_follows_level_number(number):
    level = generate_level(number, random.Random(3))
    assert len(level.enemies) == enemy_count(number)
    assert len(level.items) == useful_count(number)


def test_deeper_levels_have_more_enemies_and_less_help():
    assert enemy_count(21) > enemy_count(1)
    assert useful_count(21) < useful_count(1)
    assert useful_count(21) >= 1


@pytest.mark.parametrize("seed", range(10))
def test_every_level_has_food(seed):
    level = generate_level(21, random.Random(seed))
    assert any(i.item_type is ItemType.FOOD for i in level.items.values())


@pytest.mark.parametrize("seed", range(10))
def test_start_room_is_safe_and_exit_is_elsewhere(seed):
    level = generate_level(10, random.Random(seed))
    start_room = level.rooms[level.start_room]
    assert start_room.contains(level.start)
    assert not any(start_room.contains(e.pos) for e in level.enemies)
    assert not any(start_room.contains(p) for p in level.items)
    assert level.start_room != level.exit_room


def test_corridors_store_their_geometry():
    level = generate_level(1, random.Random(0))
    assert len(level.corridors) >= 8      # остовное дерево на 9 комнатах
    for corridor in level.corridors:
        assert corridor.cells
        assert corridor.door_a != corridor.door_b
