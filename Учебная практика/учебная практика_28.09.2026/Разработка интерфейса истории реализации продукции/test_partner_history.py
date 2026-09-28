"""Тесты истории реализации продукции: запрос, окно и переход к нему."""

import datetime
import unittest

from psycopg2 import Error as DatabaseError

import partner_history_window
from app_test_base import PARTNERS, WindowTestCase, patch_module
from partner_history_window import (PartnerHistoryWindow, format_quantity,
                                    format_sale_date)
from partner_service import get_sales_history

HISTORY_COLUMNS = (("product_name",), ("quantity",), ("sale_date",))


class RecordingCursor:
    """Курсор-заглушка: запоминает запрос и отдает одну продажу."""

    description = HISTORY_COLUMNS

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
        return [("Ламинат Дуб серый 32 класс 8 мм с фаской", 20000,
                 datetime.date(2025, 5, 18))]


class RecordingConnection:
    """Соединение-заглушка с одним записывающим курсором."""

    def __init__(self):
        self.recorded = RecordingCursor()

    def cursor(self):
        return self.recorded


class TestSalesHistoryQuery(unittest.TestCase):
    """Запрос истории продаж на поддельном соединении."""

    def test_query_joins_products_to_sales(self):
        connection = RecordingConnection()
        get_sales_history(connection, 4)
        self.assertIn("JOIN products", connection.recorded.query)

    def test_partner_id_goes_as_parameter(self):
        connection = RecordingConnection()
        get_sales_history(connection, 4)
        self.assertEqual(connection.recorded.parameters, (4,))

    def test_rows_become_dictionaries(self):
        sales = get_sales_history(RecordingConnection(), 4)
        self.assertEqual(sales[0]["quantity"], 20000)
        self.assertEqual(sales[0]["sale_date"], datetime.date(2025, 5, 18))


class TestFormatting(unittest.TestCase):
    """Значения в таблице — в понятном человеку виде."""

    def test_quantity_has_spaces_between_digit_groups(self):
        self.assertEqual(format_quantity(150000), "150 000")

    def test_small_quantity_stays_as_is(self):
        self.assertEqual(format_quantity(999), "999")

    def test_date_is_day_month_year(self):
        self.assertEqual(format_sale_date(datetime.date(2025, 3, 15)),
                         "15.03.2025")


class TestHistoryWindow(WindowTestCase):
    """Окно истории продаж и переход к нему из реестра."""

    def open_for(self, partner):
        """Выбрать партнера в реестре и нажать «История продаж»."""
        self.registry.select_partner(partner)
        self.registry.show_history()
        return self.navigator.child

    def table_rows(self, window) -> list:
        """Значения всех строк таблицы окна."""
        return [tuple(window.table.item(row, "values"))
                for row in window.table.get_children()]

    def test_history_button_waits_for_selected_partner(self):
        self.assertEqual(str(self.registry.history_button.cget("state")),
                         "disabled")
        self.registry.select_partner(PARTNERS[0])
        self.assertEqual(str(self.registry.history_button.cget("state")),
                         "normal")

    def test_button_opens_history_with_partner_id(self):
        window = self.open_for(PARTNERS[1])
        self.assertIsInstance(window, PartnerHistoryWindow)
        self.assertEqual(window.partner_id, 2)

    def test_title_names_the_partner(self):
        window = self.open_for(PARTNERS[1])
        self.assertEqual(window.title(),
                         "CRM: История реализации продукции — Большой Склад")

    def test_table_has_required_columns(self):
        window = self.open_for(PARTNERS[1])
        captions = [window.table.heading(column, "text")
                    for column in window.table["columns"]]
        self.assertEqual(captions, ["Наименование продукции",
                                    "Количество, шт.", "Дата продажи"])

    def test_rows_show_product_quantity_and_date(self):
        window = self.open_for(PARTNERS[1])
        self.assertEqual(self.table_rows(window)[0],
                         ("Ламинат Дуб дымчато-белый 33 класс 12 мм",
                          "150 000", "14.03.2026"))

    def test_summary_counts_sales_and_total(self):
        window = self.open_for(PARTNERS[1])
        self.assertEqual(window.summary.cget("text"),
                         "Продаж: 2 · всего реализовано 300 000 шт.")

    def test_partner_without_sales_gets_message(self):
        window = self.open_for(PARTNERS[2])
        self.assertEqual(self.table_rows(window), [])
        self.assertEqual(window.summary.cget("text"),
                         "Продаж у партнера пока нет.")

    def test_back_returns_to_registry_with_same_selection(self):
        self.open_for(PARTNERS[1]).go_back()
        self.registry.update()
        self.assertEqual(self.registry.state(), "normal")
        self.assertEqual(self.registry.selected["id"], 2)

    def test_selection_survives_list_reload(self):
        self.registry.select_partner(PARTNERS[1])
        self.registry.load_partners()
        self.assertEqual(self.registry.selected["id"], 2)

    def test_unknown_partner_does_not_break_window(self):
        window = self.navigator.open_history(99)
        self.assertEqual(window.title(), "CRM: История реализации продукции")
        self.assertEqual(self.table_rows(window), [])

    def test_unavailable_database_shows_error_instead_of_crash(self):
        def failing_connection():
            raise DatabaseError("could not connect to server")

        patch_module(partner_history_window,
                     get_connection=failing_connection)
        window = self.open_for(PARTNERS[1])
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertTrue(window.winfo_exists())
        self.assertEqual(self.table_rows(window), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
