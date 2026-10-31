from unittest.mock import Mock, patch

from datalayer.json_repository import JsonRepository
from presentation import app


def test_level_transition_is_saved_before_next_input(make_session, tmp_path):
    session = make_session([['@>'], ['@:>']])
    repo = JsonRepository(tmp_path)
    screen = Mock()
    inputs = iter(['d', 'q'])

    def read_key(_screen):
        key = next(inputs)
        if key == 'q':
            saved = repo.load_session()
            assert saved is not None
            assert saved.level.number == saved.stats.level_reached == 2
            assert saved.player.pos == session.level.start
        return key

    with patch.object(app, '_wait_for_big_enough_terminal', return_value=True), \
            patch.object(app, 'draw'), patch.object(app, 'read_key', side_effect=read_key):
        app.play(screen, session, repo)


def test_terminal_must_fit_the_entire_frame():
    screen = Mock()
    screen.getmaxyx.side_effect = [(24, 80), (app.MIN_ROWS, app.MIN_COLS)]
    with patch.object(app, 'put'), patch.object(app, 'read_key', return_value='x'):
        assert app._wait_for_big_enough_terminal(screen)
    screen.erase.assert_called_once()
