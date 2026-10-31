import random

from level_builder import level_from_ascii

from datalayer.json_repository import JsonRepository
from datalayer.serializers import session_from_dict, session_to_dict
from domain.commands import Move
from domain.level import KeyColor, Pos
from domain.session import GameSession


def test_doors_and_keys_are_saved(tmp_path):
    level = level_from_ascii(["@RrB:b>"], number=2)
    session = GameSession(random.Random(1), level=level)
    session.handle(Move(1, 0))
    repository = JsonRepository(tmp_path)
    repository.save_session(session)
    restored = repository.load_session()
    assert restored is not None
    assert restored.player.keys == {KeyColor.RED}
    assert restored.level.doors == level.doors
    assert restored.level.keys == level.keys
    restored.handle(Move(1, 0))
    assert restored.player.pos == Pos(2, 0)
    assert Pos(2, 0) not in restored.level.doors
    assert restored.player.keys == {KeyColor.RED}


def test_old_saves_without_keys_and_doors_still_load():
    session = GameSession(random.Random(1))
    data = session_to_dict(session)
    del data['player']['keys']
    del data['level']['doors']
    del data['level']['keys']
    restored = session_from_dict(data)
    assert restored.player.keys == set()
    assert restored.level.doors == restored.level.keys == {}


def test_special_enemy_states_and_player_sleep_survive_save(tmp_path):
    from domain.entities import EnemyKind, create_enemy

    session = GameSession(random.Random(2))
    session.player.asleep = 1
    session.level.enemies = [
        create_enemy(kind, Pos(index + 1, 1), 1)
        for index, kind in enumerate(EnemyKind)
    ]
    for enemy in session.level.enemies:
        enemy.invisible = True
        enemy.phase_turns = 7
        enemy.resting = True
        enemy.counter_ready = True
        enemy.disguised = True
    repository = JsonRepository(tmp_path)
    repository.save_session(session)
    restored = repository.load_session()
    assert restored is not None
    assert restored.player.asleep == 1
    for original, loaded in zip(session.level.enemies, restored.level.enemies):
        assert vars(loaded) == vars(original)


def test_received_hit_count_survives_save_and_old_saves_default_to_zero():
    session = GameSession(random.Random(3))
    session.stats.hits_received = 7
    data = session_to_dict(session)
    assert session_from_dict(data).stats.hits_received == 7
    del data['stats']['hits_received']
    assert session_from_dict(data).stats.hits_received == 0


def test_ghost_does_not_hide_again_after_loading(tmp_path, make_session, miss_rng):
    from domain.commands import Move
    from domain.enemies import update_ghost_visibility
    from domain.entities import EnemyKind, create_enemy

    session = make_session([['@....']], miss_rng)
    ghost = create_enemy(EnemyKind.GHOST, Pos(1, 0), 1)
    ghost.invisible = True
    session.level.enemies = [ghost]
    session.handle(Move(1, 0))
    repo = JsonRepository(tmp_path)
    repo.save_session(session)
    restored = repo.load_session()
    assert restored is not None
    ghost = restored.level.enemies[0]
    assert ghost.combat_started and not ghost.invisible
    for _ in range(30):
        update_ghost_visibility(ghost, restored.rng)
        assert not ghost.invisible


def test_old_save_without_ghost_combat_flag_loads():
    from domain.entities import EnemyKind, create_enemy

    session = GameSession(random.Random(4))
    session.level.enemies = [create_enemy(EnemyKind.GHOST, Pos(1, 1), 1)]
    data = session_to_dict(session)
    del data['level']['enemies'][0]['combat_started']
    restored = session_from_dict(data)
    assert not restored.level.enemies[0].combat_started


def test_snake_direction_survives_json_save(tmp_path, make_session):
    from domain.entities import EnemyKind, create_enemy

    session = make_session([['@....']])
    snake = create_enemy(EnemyKind.WIZZARD, Pos(3, 0), 1)
    snake.last_diagonal = (-1, 1)
    session.level.enemies = [snake]
    repo = JsonRepository(tmp_path)
    repo.save_session(session)
    restored = repo.load_session()
    assert restored is not None
    assert restored.level.enemies[0].last_diagonal == (-1, 1)
    data = session_to_dict(session)
    del data['level']['enemies'][0]['last_diagonal']
    assert session_from_dict(data).level.enemies[0].last_diagonal is None
