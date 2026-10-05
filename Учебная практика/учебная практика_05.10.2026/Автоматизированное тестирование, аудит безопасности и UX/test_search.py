"""Тесты поиска на главной форме: параметры запроса, экранирование, окно."""

import unittest

from app_test_base import PARTNERS, WindowTestCase
from partner_service import (PARTNERS_SEARCH_QUERY, like_pattern,
                             search_partners_with_discounts)

PARTNER_COLUMNS = (("id",), ("partner_type",), ("name",), ("director",),
                   ("email",), ("phone",), ("legal_address",), ("inn",),
                   ("rating",), ("total_quantity",))
INJECTION = "'; DROP TABLE partners; --"


class RecordingCursor:
    """Курсор-заглушка: запоминает запрос и параметры отдельно."""

    description = PARTNER_COLUMNS

    def __init__(self):
        self.query = None
        self.parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    def execute(self, query, parameters=None):
        self.query = query
        self.parameters = parameters

    def fetchall(self):
        return []


class RecordingConnection:
    """Соединение-заглушка с одним записывающим курсором."""

    def __init__(self):
        self.recorded = RecordingCursor()

    def cursor(self):
        return self.recorded


class TestLikePattern(unittest.TestCase):
    """Знаки шаблона LIKE из запроса пользователя — просто символы."""

    def test_text_is_searched_as_substring(self):
        self.assertEqual(like_pattern("ип"), "%ип%")

    def test_percent_is_escaped(self):
        self.assertEqual(like_pattern("100%"), "%100\\%%")

    def test_underscore_is_escaped(self):
        self.assertEqual(like_pattern("a_b"), "%a\\_b%")

    def test_backslash_is_escaped(self):
        self.assertEqual(like_pattern("a\\b"), "%a\\\\b%")


class TestSearchQuery(unittest.TestCase):
    """Текст поиска уходит в базу только параметром."""

    def test_query_text_never_changes(self):
        connection = RecordingConnection()
        search_partners_with_discounts(connection, "вектор")
        self.assertEqual(connection.recorded.query, PARTNERS_SEARCH_QUERY)
        self.assertEqual(connection.recorded.parameters,
                         {"pattern": "%вектор%"})

    def test_injection_stays_a_parameter(self):
        connection = RecordingConnection()
        search_partners_with_discounts(connection, INJECTION)
        self.assertEqual(connection.recorded.query, PARTNERS_SEARCH_QUERY)
        self.assertNotIn("DROP", connection.recorded.query)
        self.assertEqual(connection.recorded.parameters["pattern"],
                         f"%{INJECTION}%")

    def test_spaces_around_text_are_ignored(self):
        connection = RecordingConnection()
        search_partners_with_discounts(connection, "  ип  ")
        self.assertEqual(connection.recorded.parameters, {"pattern": "%ип%"})


class TestSearchBar(WindowTestCase):
    """Строка поиска в реестре."""

    def search(self, text):
        """Ввести текст и нажать «Найти»."""
        self.registry.search_entry.set_value(text)
        self.registry.load_partners()

    def test_search_shows_only_matches(self):
        self.search("склад")
        self.assertEqual([partner["name"] for partner in self.registry.partners],
                         ["Большой Склад"])
        self.assertEqual(self.registry.status.cget("text"),
                         "Найдено партнеров: 1 по запросу «склад».")

    def test_nothing_found_tells_what_to_do(self):
        self.search("нет такого")
        self.assertEqual(self.registry.partners, [])
        self.assertIn("нажмите «Сбросить»", self.registry.status.cget("text"))

    def test_reset_shows_everyone_again(self):
        self.search("склад")
        self.registry.reset_search()
        self.assertEqual(len(self.registry.partners), len(PARTNERS))
        self.assertEqual(self.registry.search_entry.get_value(), "")

    def test_selection_is_kept_if_partner_is_found(self):
        self.registry.select_partner(PARTNERS[1])
        self.search("склад")
        self.assertEqual(self.registry.selected["id"], 2)

    def test_selection_is_cleared_if_partner_is_filtered_out(self):
        self.registry.select_partner(PARTNERS[0])
        self.search("склад")
        self.assertIsNone(self.registry.selected)
        self.assertEqual(str(self.registry.history_button.cget("state")),
                         "disabled")


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
