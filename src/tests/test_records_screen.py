import unittest
from unittest.mock import Mock, patch

from domain.models.stats import RunStats
from presentation import app, records_screen


class RecordsScreenTests(unittest.TestCase):
    def screen(self, size=(24, 100)):
        screen = Mock()
        screen.getmaxyx.return_value = size
        screen.get_wch.return_value = "\n"
        return screen

    def test_empty_records(self):
        screen = self.screen()
        records_screen.show(screen, [])
        texts = [call.args[2] for call in screen.addstr.call_args_list]
        self.assertIn("Пока нет завершённых прохождений.", texts)
        screen.refresh.assert_called_once()
        screen.get_wch.assert_called_once()

    def test_all_statistics_are_displayed(self):
        screen = self.screen()
        stats = RunStats(123, 4, 5, 6, 7, 8, 9, 10, 111)
        records_screen.show(screen, [stats])
        texts = [call.args[2] for call in screen.addstr.call_args_list]
        self.assertIn(records_screen.make_row([1, 123, 4, 5, 6, 7, 8, 9, 10, 111]), texts)

    def test_small_terminal(self):
        screen = self.screen((5, 20))
        records_screen.show(screen, [RunStats()] * 10)
        for call in screen.addstr.call_args_list:
            y, x, text, _ = call.args
            self.assertTrue(0 <= y < 5)
            self.assertLessEqual(x + len(text), 19)

    def test_records_selection_returns_to_menu(self):
        screen = self.screen()
        repo = Mock()
        repo.top_records.return_value = [RunStats(treasure=42)]
        with patch.object(app.curses, "curs_set"), patch.object(app, "init_colors"), \
                patch.object(app, "log"), \
                patch.object(app.main_menu, "choose", side_effect=["records", "quit"]):
            app.run(screen, repo, Mock())
        repo.top_records.assert_called_once()
        screen.get_wch.assert_called_once()
