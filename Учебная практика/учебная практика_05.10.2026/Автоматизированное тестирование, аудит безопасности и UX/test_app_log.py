"""Тесты журнала ошибок: формат записи и события, которые туда попадают."""

import logging
import os
import re
import tempfile
import unittest
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import main_window
import material_calculator_window
import partner_edit_window
import partner_history_window
from app_log import ROOT_NAME, get_logger, setup_logging
from app_test_base import PARTNERS, WindowTestCase, patch_module

LOG_LINE = re.compile(r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2} \| ERROR \| "
                      r"Проверка журнала: нет связи с базой$")


def failing_connection():
    """Подключение, которое всегда падает, как при выключенной СУБД."""
    raise DatabaseError("could not connect to server")


class TestLogFile(unittest.TestCase):
    """Запись в файле: дата, время, уровень и понятный текст."""

    def test_line_has_date_time_and_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "app.log")
            handler = setup_logging(path)
            try:
                get_logger("test").error("Проверка журнала: %s",
                                         "нет связи с базой")
            finally:
                logging.getLogger(ROOT_NAME).removeHandler(handler)
                logging.getLogger(ROOT_NAME).setLevel(logging.NOTSET)
                handler.close()
            with open(path, encoding="utf-8") as log_file:
                lines = log_file.read().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], LOG_LINE)


class TestLoggedErrors(WindowTestCase):
    """Каждое перехваченное исключение оставляет запись в журнале."""

    def logged(self, action) -> str:
        """Выполнить действие и вернуть все записи журнала одной строкой."""
        with self.assertLogs(ROOT_NAME, level="WARNING") as captured:
            action()
        return "\n".join(captured.output)

    def test_registry_without_database(self):
        patch_module(main_window, get_connection=failing_connection)
        output = self.logged(self.registry.load_partners)
        self.assertIn("ERROR", output)
        self.assertIn("Реестр не загружен", output)
        self.assertIn("could not connect to server", output)

    def test_card_not_saved_without_database(self):
        patch_module(partner_edit_window, get_connection=failing_connection)
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.fields["rating"].set_value(9)
        output = self.logged(editor.save)
        self.assertIn("Карточка партнера не сохранена", output)

    def test_card_with_invalid_rating(self):
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.fields["rating"].set_value("пять")
        output = self.logged(editor.save)
        self.assertIn("WARNING", output)
        self.assertIn("Рейтинг должен быть целым числом", output)

    def test_history_without_database(self):
        patch_module(partner_history_window,
                     get_connection=failing_connection)
        output = self.logged(lambda: self.navigator.open_history(2))
        self.assertIn("История продаж партнера № 2 не загружена", output)

    def test_calculation_that_returned_minus_one(self):
        window = self.navigator.open_calculator()
        window.fields["quantity"].set_value("-10")
        window.fields["param_1"].set_value("2,5")
        window.fields["param_2"].set_value("1,2")
        output = self.logged(window.calculate)
        self.assertIn("вернул -1", output)
        self.assertIn("Количество продукции", output)

    def test_calculation_without_database(self):
        window = self.navigator.open_calculator()
        patch_module(material_calculator_window,
                     get_connection=failing_connection)
        output = self.logged(window.calculate)
        self.assertIn("Расчет материалов не выполнен", output)

    def test_unexpected_error_in_button_is_logged_and_shown(self):
        broken = ttk.Button(self.registry, command=lambda: 1 / 0)
        output = self.logged(broken.invoke)
        self.assertIn("Непредвиденная ошибка", output)
        self.assertIn("ZeroDivisionError", output)
        self.assertEqual(self.dialog_kinds(), ["error"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
