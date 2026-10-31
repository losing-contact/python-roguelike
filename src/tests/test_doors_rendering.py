from unittest.mock import patch

from level_builder import level_from_ascii

from domain.level import KeyColor, Pos
from domain.session import GameSession
from presentation.renderer import draw, draw_hud
from presentation.theme import DOOR_CHAR, KEY_CHAR


class Screen:
    def clear(self):
        pass

    def refresh(self):
        pass


def test_doors_are_remembered_but_keys_require_visibility():
    session = GameSession(level=level_from_ascii(['@rRB>']))
    session.visible = {Pos(2, 0)}
    session.exploration.seen = {Pos(1, 0), Pos(2, 0), Pos(3, 0)}
    with patch('presentation.renderer.draw_frame'), \
            patch('presentation.renderer.draw_hud'), \
            patch('presentation.renderer.put_map') as put_map:
        draw(Screen(), session, [])
    doors = [call for call in put_map.call_args_list if call.args[2].char == DOOR_CHAR]
    keys = [call for call in put_map.call_args_list if call.args[2].char == KEY_CHAR]
    assert len(doors) == 1 and doors[0].kwargs['dim']
    assert [call.args[1] for call in keys] == [Pos(2, 0)]


def test_hud_displays_collected_keys_before_long_weapon_name():
    session = GameSession(level=level_from_ascii(['@:>']))
    session.player.keys = {KeyColor.RED, KeyColor.BLUE}
    with patch('presentation.renderer.attr', return_value=0), \
            patch('presentation.renderer.put'), \
            patch('presentation.renderer.put_segments') as segments:
        draw_hud(Screen(), session, [], 21, 78)
    status = ''.join(text for text, _ in segments.call_args_list[0].args[3])
    assert 'КЛЮЧИ = = ' in status
    assert status.index('КЛЮЧИ') < status.index('ОРУЖИЕ')


def test_explored_room_remembers_walls_but_hides_floor_and_actors():
    from domain.entities import EnemyKind, create_enemy
    from domain.items import Item, ItemType

    session = GameSession(level=level_from_ascii(['#####', '#@..#', '#####']))
    session.level.enemies = [create_enemy(EnemyKind.ZOMBIE, Pos(3, 1), 1)]
    session.level.items[Pos(2, 1)] = Item(ItemType.FOOD, 'Яблоко', health=10)
    session.visible = {session.player.pos}
    session.exploration.seen = {Pos(0, 1), Pos(1, 1), Pos(2, 1), Pos(3, 1)}
    with patch('presentation.renderer.draw_frame'), \
            patch('presentation.renderer.draw_hud'), \
            patch('presentation.renderer.put_map') as put_map:
        draw(Screen(), session, [])
    positions = {call.args[1] for call in put_map.call_args_list}
    assert positions == {Pos(0, 1), session.player.pos}
    wall = next(call for call in put_map.call_args_list if call.args[1] == Pos(0, 1))
    assert wall.kwargs['dim']
