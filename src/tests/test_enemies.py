from dataclasses import replace
from unittest.mock import patch

import pytest

from domain import events as ev
from domain.enemies import PATTERNS, diagonal_walk, two_step_walk
from domain.entities import EnemyKind, create_enemy
from domain.level import KeyColor, Pos, Room

ROOM = [
    '#########',
    '#.......#',
    '#.......#',
    '#.@.....#',
    '#.......#',
    '#.......#',
    '#########',
]


@pytest.mark.parametrize('kind', list(EnemyKind))
def test_all_enemies_chase_by_one_orthogonal_step(make_session, kind):
    session = make_session([ROOM])
    session.level.rooms = [Room(0, 1, 1, 7, 5, 0, 0)]
    enemy = create_enemy(kind, Pos(5, 3), 1)
    enemy.disguised = False
    enemy.spec = replace(enemy.spec, move_every=1, hostility=10)
    session.level.enemies = [enemy]
    session._enemy_turn(enemy, [])
    assert enemy.pos == Pos(4, 3)


@pytest.mark.parametrize('kind', list(EnemyKind))
def test_no_path_through_a_locked_door_uses_normal_pattern(make_session, kind):
    session = make_session([['@::r:::>']])
    enemy = create_enemy(kind, Pos(5, 0), 1)
    enemy.disguised = False
    enemy.spec = replace(enemy.spec, move_every=1, hostility=10)
    session.level.enemies = [enemy]
    with patch.dict(PATTERNS, {kind: lambda *_: Pos(6, 0)}):
        session._enemy_turn(enemy, [])
    assert enemy.pos == Pos(6, 0)
    assert session.level.doors == {Pos(3, 0): KeyColor.RED}


def test_chase_range_uses_path_length_around_walls(make_session):
    session = make_session([['@#...', '.#...', '.....']])
    enemy = create_enemy(EnemyKind.ZOMBIE, Pos(2, 0), 1)
    enemy.spec = replace(enemy.spec, move_every=1, hostility=2)
    session.level.enemies = [enemy]
    # По прямой две клетки, но обход стены длиннее радиуса враждебности.
    with patch.dict(PATTERNS, {enemy.kind: lambda *_: Pos(3, 0)}):
        session._enemy_turn(enemy, [])
    assert enemy.pos == Pos(3, 0)


def test_snake_does_not_attack_diagonally_while_chasing(make_session):
    session = make_session([ROOM])
    session.level.rooms = [Room(0, 1, 1, 7, 5, 0, 0)]
    enemy = create_enemy(EnemyKind.WIZZARD, Pos(3, 2), 1)
    enemy.spec = replace(enemy.spec, move_every=1)
    session.level.enemies = [enemy]
    events = []
    session._enemy_turn(enemy, events)
    assert not any(isinstance(event, ev.EnemyAttacked) for event in events)
    assert enemy.pos.manhattan(session.player.pos) == 1


def test_ogre_rests_once_then_counterattacks_without_extra_delay(make_session, miss_rng):
    session = make_session([ROOM], miss_rng)
    enemy = create_enemy(EnemyKind.OGRE, Pos(3, 3), 1)
    enemy.timer = enemy.spec.move_every - 1
    session.level.enemies = [enemy]
    events = []
    session._enemy_turn(enemy, events)
    assert len(events) == 1 and not events[0].hit
    assert enemy.resting

    events = []
    session._enemy_turn(enemy, events)
    assert events == []
    assert enemy.counter_ready and not enemy.resting

    session._enemy_turn(enemy, events)
    assert len(events) == 1 and events[0].hit  # даже при генераторе постоянных промахов
    assert enemy.resting and not enemy.counter_ready


def test_idle_ogre_keeps_two_cell_walk(make_session):
    session = make_session([ROOM])
    enemy = create_enemy(EnemyKind.OGRE, Pos(5, 3), 1)
    session.level.enemies = [enemy]
    target = two_step_walk(enemy, session.level, session.rng)
    assert target is not None
    assert enemy.pos.manhattan(target) == 2


def test_idle_snake_keeps_diagonal_walk(make_session):
    session = make_session([ROOM])
    enemy = create_enemy(EnemyKind.WIZZARD, Pos(5, 3), 1)
    session.level.enemies = [enemy]
    target = diagonal_walk(enemy, session.level, session.rng)
    assert target is not None
    assert abs(target.x - enemy.pos.x) == abs(target.y - enemy.pos.y) == 1


@pytest.mark.parametrize('player_attacks', [True, False])
def test_ghost_stays_visible_after_a_missed_attack(make_session, miss_rng, player_attacks):
    from domain import combat
    from domain.enemies import update_ghost_visibility

    session = make_session([ROOM], miss_rng)
    ghost = create_enemy(EnemyKind.GHOST, Pos(3, 3), 1)
    ghost.invisible = True
    ghost.phase_turns = 1
    attacker, target = (session.player, ghost) if player_attacks else (ghost, session.player)
    result = combat.resolve_attack(attacker, target, session.rng)
    assert not result.hit
    assert not ghost.invisible
    assert ghost.combat_started
    for _ in range(30):
        update_ghost_visibility(ghost, session.rng)
        assert not ghost.invisible


def test_ghost_changes_visibility_before_combat():
    import random

    from domain.enemies import update_ghost_visibility

    ghost = create_enemy(EnemyKind.GHOST, Pos(1, 1), 1)
    ghost.phase_turns = 1
    rng = random.Random(1)
    update_ghost_visibility(ghost, rng)
    assert ghost.invisible
    ghost.phase_turns = 1
    update_ghost_visibility(ghost, rng)
    assert not ghost.invisible


def test_non_ghost_visibility_is_not_changed_by_attack(make_session, hit_rng):
    from domain import combat

    session = make_session([ROOM], hit_rng)
    zombie = create_enemy(EnemyKind.ZOMBIE, Pos(3, 3), 1)
    combat.resolve_attack(session.player, zombie, session.rng)
    assert not zombie.combat_started


def test_snake_changes_direction_when_another_diagonal_is_free(make_session):
    session = make_session([ROOM])
    snake = create_enemy(EnemyKind.WIZZARD, Pos(5, 3), 1)
    snake.last_diagonal = (1, 1)
    with patch.object(session.rng, "choice", side_effect=lambda cells: cells[0]):
        target = diagonal_walk(snake, session.level, session.rng)
    assert target is not None
    assert (target.x - snake.pos.x, target.y - snake.pos.y) != (1, 1)


def test_snake_can_keep_direction_when_it_is_the_only_way(make_session):
    session = make_session([['###@', '#.##', '##.#', '####']])
    snake = create_enemy(EnemyKind.WIZZARD, Pos(1, 1), 1)
    snake.last_diagonal = (1, 1)
    assert diagonal_walk(snake, session.level, session.rng) == Pos(2, 2)


def test_snake_falls_back_to_normal_step_in_a_narrow_corridor(make_session):
    session = make_session([['####@', '#:::#', '#####']])
    snake = create_enemy(EnemyKind.WIZZARD, Pos(1, 1), 1)
    assert diagonal_walk(snake, session.level, session.rng) == Pos(2, 1)


def test_snake_remembers_direction_after_an_actual_idle_step(make_session):
    session = make_session([ROOM])
    snake = create_enemy(EnemyKind.WIZZARD, Pos(5, 3), 1)
    snake.spec = replace(snake.spec, move_every=1, hostility=0)
    session.level.enemies = [snake]
    previous = snake.pos
    session._enemy_turn(snake, [])
    assert snake.last_diagonal == (snake.pos.x - previous.x, snake.pos.y - previous.y)


def test_snake_has_very_high_agility_and_high_hostility():
    from domain.entities import SPECS

    snake = SPECS[EnemyKind.WIZZARD]
    assert snake.agility > max(spec.agility for kind, spec in SPECS.items()
                              if kind is not EnemyKind.WIZZARD)
    assert snake.hostility >= SPECS[EnemyKind.VAMPIRE].hostility


def test_mimic_waits_disguised_then_reveals_and_attacks(make_session, hit_rng):
    session = make_session([ROOM], hit_rng)
    mimic = create_enemy(EnemyKind.MIMIC, Pos(6, 3), 1)
    mimic.spec = replace(mimic.spec, move_every=1)
    session.level.enemies = [mimic]
    events = []
    session._enemy_turn(mimic, events)
    assert mimic.disguised and mimic.pos == Pos(6, 3) and events == []

    mimic.pos = Pos(3, 3)
    session._enemy_turn(mimic, events)
    assert not mimic.disguised
    assert events[0] == ev.MimicRevealed()
    assert isinstance(events[1], ev.EnemyAttacked)


def test_snake_hit_causes_one_skipped_player_action(make_session, hit_rng):
    from domain import combat
    from domain.commands import Move

    session = make_session([ROOM], hit_rng)
    snake = create_enemy(EnemyKind.WIZZARD, Pos(3, 3), 1)
    result = combat.resolve_attack(snake, session.player, session.rng)
    assert result.slept and session.player.asleep == 1
    previous = session.player.pos
    assert session.handle(Move(1, 0)) == [ev.PlayerSlept()]
    assert session.player.pos == previous and session.player.asleep == 0
    session.handle(Move(1, 0))
    assert session.player.pos == previous.shifted(1, 0)
