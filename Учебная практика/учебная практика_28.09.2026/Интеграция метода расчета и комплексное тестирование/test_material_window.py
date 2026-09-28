"""Комплексные тесты окна расчета материалов: итог и ошибки ввода."""

import unittest
from decimal import Decimal

from psycopg2 import Error as DatabaseError

import material_calculator_window
from app_test_base import (MATERIAL_TYPES, PRODUCT_TYPES, WindowTestCase,
                           catalog_of, patch_module)
from material_calculator import (MATERIAL_TYPE_PROBLEM, PARAMETERS_PROBLEM,
                                 PRODUCT_TYPE_PROBLEM, QUANTITY_PROBLEM)
from material_calculator_window import (EMPTY_RESULT,
                                        MaterialCalculatorWindow,
                                        format_amount, format_decimal,
                                        parse_number, parse_whole)


def failing_connection():
    """Подключение, которое всегда падает, как при выключенной СУБД."""
    raise DatabaseError("could not connect to server")


class TestFormHelpers(unittest.TestCase):
    """Разбор полей формы и вывод чисел."""

    def test_whole_number_is_parsed(self):
        self.assertEqual(parse_whole(" 250 "), 250)

    def test_text_goes_to_method_as_is(self):
        self.assertEqual(parse_whole("сто"), "сто")

    def test_comma_is_a_decimal_separator(self):
        self.assertEqual(parse_number("2,5"), 2.5)

    def test_point_is_a_decimal_separator_too(self):
        self.assertEqual(parse_number("1.2"), 1.2)

    def test_amount_has_spaces_between_digit_groups(self):
        self.assertEqual(format_amount(1765), "1 765")

    def test_fraction_is_written_with_comma(self):
        self.assertEqual(format_decimal(Decimal("2.35")), "2,35")


class TestCalculatorWindow(WindowTestCase):
    """Окно расчета: итог на экране и обработка -1 без падений."""

    def open_calculator(self, quantity="250", param_1="2,5", param_2="1,2"):
        """Открыть расчет из реестра и заполнить поля формы."""
        self.registry.open_calculator()
        window = self.navigator.child
        window.fields["quantity"].set_value(quantity)
        window.fields["param_1"].set_value(param_1)
        window.fields["param_2"].set_value(param_2)
        return window

    def check_failure(self, window, problem):
        """Расчет вернул -1: окно живо, итога нет, причина показана."""
        window.calculate()
        self.assertTrue(window.winfo_exists())
        self.assertEqual(window.result_label.cget("text"), EMPTY_RESULT)
        self.assertEqual(self.dialogs, [("error", problem)])

    def test_registry_opens_calculator_window(self):
        window = self.open_calculator()
        self.assertIsInstance(window, MaterialCalculatorWindow)
        self.assertEqual(window.title(), "CRM: Расчет материалов")

    def test_lists_are_filled_from_catalog(self):
        window = self.open_calculator()
        self.assertEqual(len(window.fields["product_type"].cget("values")),
                         len(PRODUCT_TYPES))
        self.assertEqual(window.fields["material_type"].get_value(), 1)

    def test_correct_data_shows_result(self):
        window = self.open_calculator()
        window.calculate()
        self.assertEqual(window.result_label.cget("text"), "1 765")
        self.assertEqual(self.dialogs, [])

    def test_other_types_change_result(self):
        window = self.open_calculator(quantity="100", param_1="1,5",
                                      param_2="0,8")
        window.fields["product_type"].set_value(3)
        window.fields["material_type"].set_value(2)
        window.calculate()
        self.assertEqual(window.result_label.cget("text"), "526")

    def test_negative_quantity(self):
        self.check_failure(self.open_calculator(quantity="-10"),
                           QUANTITY_PROBLEM)

    def test_zero_quantity(self):
        self.check_failure(self.open_calculator(quantity="0"),
                           QUANTITY_PROBLEM)

    def test_quantity_written_in_words(self):
        self.check_failure(self.open_calculator(quantity="сто"),
                           QUANTITY_PROBLEM)

    def test_fractional_quantity(self):
        self.check_failure(self.open_calculator(quantity="2,5"),
                           QUANTITY_PROBLEM)

    def test_negative_parameter(self):
        self.check_failure(self.open_calculator(param_1="-2,5"),
                           PARAMETERS_PROBLEM)

    def test_zero_parameter(self):
        self.check_failure(self.open_calculator(param_2="0"),
                           PARAMETERS_PROBLEM)

    def test_empty_parameter(self):
        self.check_failure(self.open_calculator(param_1=""),
                           PARAMETERS_PROBLEM)

    def test_product_type_removed_from_catalog(self):
        patch_module(material_calculator_window,
                     DatabaseCatalog=lambda connection:
                     catalog_of(PRODUCT_TYPES[1:], MATERIAL_TYPES))
        self.check_failure(self.open_calculator(), PRODUCT_TYPE_PROBLEM)

    def test_material_type_removed_from_catalog(self):
        patch_module(material_calculator_window,
                     DatabaseCatalog=lambda connection:
                     catalog_of(PRODUCT_TYPES, MATERIAL_TYPES[1:]))
        self.check_failure(self.open_calculator(), MATERIAL_TYPE_PROBLEM)

    def test_old_result_disappears_after_error(self):
        window = self.open_calculator()
        window.calculate()
        window.fields["quantity"].set_value("-1")
        window.calculate()
        self.assertEqual(window.result_label.cget("text"), EMPTY_RESULT)

    def test_database_error_during_calculation(self):
        window = self.open_calculator()
        patch_module(material_calculator_window,
                     get_connection=failing_connection)
        window.calculate()
        self.assertTrue(window.winfo_exists())
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIn("PostgreSQL", self.dialogs[0][1])

    def test_database_error_when_opening(self):
        patch_module(material_calculator_window,
                     get_connection=failing_connection)
        window = self.open_calculator()
        self.assertTrue(window.winfo_exists())
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIsNone(window.fields["product_type"].get_value())

    def test_back_returns_to_registry(self):
        window = self.open_calculator()
        window.go_back()
        self.registry.update()
        self.assertFalse(window.winfo_exists())
        self.assertEqual(self.registry.state(), "normal")


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
