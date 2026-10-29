import random

import pytest
from level_builder import level_from_ascii

from domain.generation.level_factory import generate_level
from domain.generation.locks import (
    can_pass,
    collect_keys,
    lock_count,
    lock_problems,
    place_keys,
    rooms_connected,
)
from domain.generation.validate import find_problems
from domain.geometry import bfs_distances
from domain.models.keys import KeyColor
from domain.models.position import Pos

# В картах: 0 - стартовая комната, r/y/b - запертые двери, R/Y/B - ключи, > - выход


def level(row):
    """Одна строка = коридор из клеток. Игрок начинает в самой левой (комната 0)."""
    return level_from_ascii([row], start=Pos(0, 0))


# --- проверка, что уровень можно пройти -------------------------------------
def test_level_without_doors_is_fine():
    assert lock_problems(level("0:::>")) == []


def test_key_before_its_door_is_fine():
    assert lock_problems(level("0R+:r:>")) == []


def test_key_behind_its_own_door_is_a_softlock():
    problems = lock_problems(level("0:r:R:>"))
    assert "до выхода не дойти, даже собрав все достижимые ключи" in problems
    assert "до ключа red не дойти" in problems


def test_door_without_any_key_is_a_softlock():
    problems = lock_problems(level("0:r:>"))
    assert "до ключа red не дойти" in problems


def test_keys_can_open_each_other_in_a_chain():
    # жёлтый ключ открывает жёлтую дверь, за ней красный ключ, он открывает красную дверь
    assert lock_problems(level("0:Y:y:R:r:>")) == []


def test_two_doors_that_need_each_others_keys_are_a_softlock():
    # красный ключ лежит за жёлтой дверью, а жёлтый за красной: ни один не достать
    problems = lock_problems(level("0:y:R:r:Y:>"))
    assert problems != []
    assert "до ключа red не дойти" in problems
    assert "до ключа yellow не дойти" in problems


def test_one_key_can_be_unreachable_while_the_exit_is_fine():
    # синяя дверь в тупике, ключ от неё лежит за ней самой, но выход и без неё доступен
    problems = lock_problems(level("0:>:b:B"))
    assert problems == ["до ключа blue не дойти"]


def test_door_must_stand_in_a_doorway():
    broken = level("0:::>")
    broken.doors[Pos(2, 0)] = KeyColor.RED       # клетка 2 - коридор, а не проём
    broken.keys[Pos(1, 0)] = KeyColor.RED
    assert any("не в проёме" in p for p in lock_problems(broken))


def test_nothing_may_lie_on_a_key():
    lv = level("0R+:r:>")
    lv.items[Pos(1, 0)] = object()
    assert any("лежит или стоит" in p for p in lock_problems(lv))


# --- поиск в ширину с ключами -----------------------------------------------
def test_a_locked_door_blocks_the_search_until_the_key_is_found():
    lv = level("0:r:>")
    assert Pos(4, 0) not in bfs_distances(lv.start, can_pass(lv, keys=set()))
    assert Pos(4, 0) in bfs_distances(lv.start, can_pass(lv, keys={KeyColor.RED}))


def test_a_key_of_another_color_does_not_open_the_door():
    lv = level("0:r:>")
    assert Pos(4, 0) not in bfs_distances(lv.start, can_pass(lv, keys={KeyColor.BLUE}))


def test_collect_keys_returns_what_can_be_picked_up():
    seen, keys = collect_keys(level("0:Y:y:R:r:>"))
    assert keys == {KeyColor.YELLOW, KeyColor.RED}
    assert Pos(10, 0) in seen                      # выход


def test_collect_keys_stops_at_the_deadlock():
    seen, keys = collect_keys(level("0:y:R:r:Y:>"))
    assert keys == set()
    assert Pos(1, 0) in seen                       # до первой двери дойти можно
    assert Pos(10, 0) not in seen                  # а до выхода нет


def test_doors_do_not_let_an_enemy_pass():
    lv = level("0:r:>")
    assert not lv.is_walkable(Pos(2, 0))
    assert not lv.can_enemy_enter(Pos(2, 0))
    del lv.doors[Pos(2, 0)]
    assert lv.is_walkable(Pos(2, 0))


# --- сколько дверей ---------------------------------------------------------
def test_no_doors_on_the_first_level_and_more_deeper():
    assert lock_count(1) == 0
    assert lock_count(2) == 1
    assert lock_count(5) == 2
    assert lock_count(8) == lock_count(21) == len(KeyColor)


# --- сгенерированные уровни -------------------------------------------------
@pytest.mark.parametrize("seed", range(25))
@pytest.mark.parametrize("number", (2, 5, 8, 21))
def test_generated_levels_with_doors_can_be_finished(seed, number):
    lv = generate_level(number, random.Random(seed))
    assert find_problems(lv) == []
    assert len(lv.doors) <= lock_count(number)
    assert set(lv.doors.values()) <= set(lv.keys.values())     # у каждой двери есть ключ
    assert len(lv.keys) == len(lv.doors)


def test_the_first_level_has_no_doors():
    for seed in range(20):
        lv = generate_level(1, random.Random(seed))
        assert lv.doors == {} and lv.keys == {}


def test_most_deep_levels_do_get_their_doors():
    counts = [len(generate_level(10, random.Random(seed)).doors) for seed in range(60)]
    full = sum(1 for c in counts if c == lock_count(10))
    empty = sum(1 for c in counts if c == 0)
    assert full >= 35    # хотя бы 3 уровня из 5 получают полный набор дверей
    assert empty <= 10   # и мало уровней остаётся вовсе без дверей


def test_doors_actually_stand_in_the_way():
    """На большинстве уровней с дверями выход без ключей недостижим.

    Исключения бывают, когда к выходу ведут два пути: тогда запирается только боковой тупик.
    """
    blocked = total = 0
    for seed in range(60):
        lv = generate_level(8, random.Random(seed))
        if not lv.doors:
            continue
        total += 1
        if lv.exit not in bfs_distances(lv.start, can_pass(lv, keys=set())):
            blocked += 1
    assert total > 40
    assert blocked >= total * 0.8


def test_keys_are_never_in_the_start_room_or_on_something():
    for seed in range(40):
        lv = generate_level(9, random.Random(seed))
        start_room = lv.rooms[lv.start_room]
        for pos in lv.keys:
            assert not start_room.contains(pos)
            assert pos not in lv.items and lv.enemy_at(pos) is None and pos != lv.exit


def test_removing_a_key_makes_the_level_unfinishable():
    for seed in range(40):
        lv = generate_level(9, random.Random(seed))
        if lv.keys:
            lv.keys.popitem()
            assert lock_problems(lv) != []
            return
    pytest.fail("не нашлось уровня с ключами")


def test_a_key_in_the_start_room_is_rejected():
    for seed in range(40):
        lv = generate_level(9, random.Random(seed))
        if lv.keys:
            color = next(iter(lv.keys.values()))
            lv.keys.clear()
            lv.keys[lv.start] = color
            assert lock_problems(lv) != []
            return
    pytest.fail("не нашлось уровня с ключами")


# --- как кладутся ключи и ставятся двери ------------------------------------
def test_key_is_placed_only_where_the_player_can_already_reach():
    lv = level("0.r" + "." * 20)                     # слева от двери одна клетка, справа двадцать
    free = [Pos(x, 0) for x in range(1, 23) if x != 2]
    for seed in range(20):
        lv.keys = {}
        assert place_keys(lv, random.Random(seed), [KeyColor.RED], free)
        assert list(lv.keys) == [Pos(1, 0)]


def test_no_place_for_a_key_means_failure():
    lv = level("0r" + "." * 5)
    free = [Pos(x, 0) for x in range(2, 7)]          # все свободные клетки за дверью
    assert not place_keys(lv, random.Random(1), [KeyColor.RED], free)


def test_doors_stand_only_on_corridors_that_cannot_be_bypassed():
    checked = 0
    for seed in range(40):
        lv = generate_level(9, random.Random(seed))
        for pos in lv.doors:
            corridor = next(c for c in lv.corridors if pos in (c.door_a, c.door_b))
            assert not rooms_connected(lv, corridor, corridor.room_a, corridor.room_b)
            checked += 1
    assert checked > 40
