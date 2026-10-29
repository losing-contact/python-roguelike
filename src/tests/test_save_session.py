import random

from level_builder import level_from_ascii

from datalayer.json_repository import JsonRepository
from datalayer.serializers import session_from_dict, session_to_dict
from domain.commands import Move
from domain.models.keys import KeyColor
from domain.models.position import Pos
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
