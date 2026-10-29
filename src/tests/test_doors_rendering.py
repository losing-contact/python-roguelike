from unittest.mock import patch

from level_builder import level_from_ascii

from domain.models.keys import KeyColor
from domain.models.position import Pos
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
