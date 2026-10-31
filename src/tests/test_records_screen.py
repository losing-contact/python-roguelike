import unittest
from unittest.mock import Mock, patch

from domain.stats import RunStats
from presentation import app, screens


class RecordsScreenTests(unittest.TestCase):
    def screen(self, size=(24, 100)):
        screen = Mock()
        screen.getmaxyx.return_value = size
        screen.get_wch.return_value = "\n"
        return screen

    def test_empty_records(self):
        screen = self.screen()
        screens.show_records(screen, [])
        texts = [call.args[2] for call in screen.addstr.call_args_list]
        self.assertIn("Пока нет завершённых прохождений.", texts)
        screen.refresh.assert_called_once()
        screen.get_wch.assert_called_once()

    def test_all_statistics_are_displayed(self):
        screen = self.screen()
        stats = RunStats(
            treasure=123, level_reached=4, enemies_killed=5, food_eaten=6,
            elixirs_drunk=7, scrolls_read=8, hits_dealt=9, hits_received=10, steps=111,
        )
        screens.show_records(screen, [stats])
        texts = [call.args[2] for call in screen.addstr.call_args_list]
        self.assertIn(screens.make_row([1, 123, 4, 5, 6, 7, 8, 9, 10, 111]), texts)

    def test_small_terminal(self):
        screen = self.screen((5, 20))
        screens.show_records(screen, [RunStats()] * 10)
        for call in screen.addstr.call_args_list:
            y, x, text, _ = call.args
            self.assertTrue(0 <= y < 5)
            self.assertLessEqual(x + len(text), 19)

    def test_records_selection_returns_to_menu(self):
        screen = self.screen()
        repo = Mock()
        repo.top_records.return_value = [RunStats(treasure=42)]
        with patch.object(app.curses, "curs_set"), patch.object(app, "init_colors"), \
                patch.object(app.menus, "choose_main", side_effect=["records", "quit"]):
            app.run(screen, repo, Mock())
        repo.top_records.assert_called_once()
        screen.get_wch.assert_called_once()


def test_records_are_sorted_by_treasure_then_level(tmp_path):
    from datalayer.json_repository import JsonRepository

    repo = JsonRepository(tmp_path)
    for treasure, level in [(30, 2), (80, 1), (30, 5)]:
        repo.add_record(RunStats(treasure=treasure, level_reached=level))
    assert [(r.treasure, r.level_reached) for r in repo.top_records(2)] == [(80, 1), (30, 5)]
