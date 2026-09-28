"""Unit-тесты метода расчета материалов: обычный расчет и крайние случаи.

Справочники — мок-объект MemoryCatalog со значениями из schema.sql,
поэтому база данных для тестов не нужна.
"""

import math
import unittest
from decimal import Decimal

from material_calculator import (ERROR_RESULT, MATERIAL_TYPE_PROBLEM,
                                 PARAMETERS_PROBLEM, PRODUCT_TYPE_PROBLEM,
                                 QUANTITY_PROBLEM, DatabaseCatalog,
                                 MaterialCalculator, MemoryCatalog,
                                 get_material_types, get_product_types)

LAMINATE = 1
PARQUET = 3
CORK = 4
MATERIAL_1 = 1
MATERIAL_2 = 2
MATERIAL_5 = 5

COEFFICIENTS = {
    1: Decimal("2.35"),
    2: Decimal("5.15"),
    3: Decimal("4.34"),
    4: Decimal("1.50"),
}
DEFECT_PERCENTS = {
    1: Decimal("0.10"),
    2: Decimal("0.95"),
    3: Decimal("0.28"),
    4: Decimal("0.55"),
    5: Decimal("0.34"),
}


def make_calculator() -> MaterialCalculator:
    """Калькулятор со справочниками из schema.sql в памяти."""
    return MaterialCalculator(MemoryCatalog(COEFFICIENTS, DEFECT_PERCENTS))


class TestRequiredCases(unittest.TestCase):
    """Пять обязательных тест-кейсов из задания."""

    def setUp(self):
        self.calculator = make_calculator()

    def test_1_standard_calculation(self):
        # 2,5 × 1,2 × 2,35 = 7,05; × 250 = 1762,5; × 1,001 = 1764,2625.
        result = self.calculator.calculate_material(
            LAMINATE, MATERIAL_1, 250, 2.5, 1.2)
        self.assertEqual(result, 1765)

    def test_2_fraction_is_rounded_up(self):
        # 1764,2625 при обычном округлении дал бы 1764, а нужно 1765.
        result = self.calculator.calculate_material(
            LAMINATE, MATERIAL_1, 250, 2.5, 1.2)
        self.assertEqual(round(1764.2625), 1764)
        self.assertEqual(result, math.ceil(1764.2625))

    def test_3_unknown_type_gives_minus_one(self):
        cases = {"тип продукции": (99, MATERIAL_1),
                 "тип материала": (LAMINATE, 99)}
        for case, (product_type_id, material_type_id) in cases.items():
            with self.subTest(case=case):
                result = self.calculator.calculate_material(
                    product_type_id, material_type_id, 250, 2.5, 1.2)
                self.assertEqual(result, ERROR_RESULT)

    def test_4_negative_parameters_give_minus_one(self):
        cases = {"param_1": (-2.5, 1.2), "param_2": (2.5, -1.2)}
        for case, (param_1, param_2) in cases.items():
            with self.subTest(case=case):
                result = self.calculator.calculate_material(
                    LAMINATE, MATERIAL_1, 250, param_1, param_2)
                self.assertEqual(result, ERROR_RESULT)

    def test_5_zero_or_negative_quantity_gives_minus_one(self):
        for quantity in (0, -1, -250):
            with self.subTest(quantity=quantity):
                result = self.calculator.calculate_material(
                    LAMINATE, MATERIAL_1, quantity, 2.5, 1.2)
                self.assertEqual(result, ERROR_RESULT)


class TestCalculationDetails(unittest.TestCase):
    """Точность расчета и остальные расчеты из справочника."""

    def setUp(self):
        self.calculator = make_calculator()

    def test_other_types_from_catalog(self):
        cases = ((PARQUET, MATERIAL_2, 100, 1.5, 0.8, 526),
                 (CORK, MATERIAL_5, 40, 3.0, 2.0, 362))
        for *arguments, expected in cases:
            with self.subTest(arguments=arguments):
                self.assertEqual(
                    self.calculator.calculate_material(*arguments), expected)

    def test_whole_result_is_not_rounded_up_by_float_error(self):
        # Во float 100 × (1 + 10 / 100) = 110.00000000000001 → 111.
        calculator = MaterialCalculator(
            MemoryCatalog({1: Decimal("1")}, {1: Decimal("10")}))
        self.assertEqual(calculator.calculate_material(1, 1, 10, 2, 5), 110)

    def test_small_fraction_still_adds_a_unit(self):
        calculator = MaterialCalculator(
            MemoryCatalog({1: Decimal("1")}, {1: Decimal("0")}))
        self.assertEqual(calculator.calculate_material(1, 1, 1, 2.01, 1), 3)

    def test_result_is_an_int(self):
        result = self.calculator.calculate_material(
            LAMINATE, MATERIAL_1, 250, 2.5, 1.2)
        self.assertIs(type(result), int)

    def test_decimal_parameters_are_accepted(self):
        result = self.calculator.calculate_material(
            LAMINATE, MATERIAL_1, 250, Decimal("2.5"), Decimal("1.2"))
        self.assertEqual(result, 1765)


class TestBadInput(unittest.TestCase):
    """Любой неверный ввод дает -1, а не исключение."""

    def setUp(self):
        self.calculator = make_calculator()

    def calculate(self, product_type_id=LAMINATE, material_type_id=MATERIAL_1,
                  quantity=250, param_1=2.5, param_2=1.2):
        """Расчет с верными значениями по умолчанию и одной подменой."""
        return self.calculator.calculate_material(
            product_type_id, material_type_id, quantity, param_1, param_2)

    def test_zero_parameter(self):
        self.assertEqual(self.calculate(param_1=0), ERROR_RESULT)

    def test_text_instead_of_numbers(self):
        self.assertEqual(self.calculate(quantity="250"), ERROR_RESULT)
        self.assertEqual(self.calculate(param_2="1,2"), ERROR_RESULT)

    def test_fractional_quantity(self):
        self.assertEqual(self.calculate(quantity=2.5), ERROR_RESULT)

    def test_bool_is_not_a_number_here(self):
        self.assertEqual(self.calculate(quantity=True), ERROR_RESULT)
        self.assertEqual(self.calculate(param_1=True), ERROR_RESULT)

    def test_nan_and_infinity(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.assertEqual(self.calculate(param_1=value), ERROR_RESULT)

    def test_missing_values(self):
        self.assertEqual(self.calculate(product_type_id=None), ERROR_RESULT)
        self.assertEqual(self.calculate(quantity=None), ERROR_RESULT)

    def test_text_type_id_never_reaches_catalog(self):
        class StrictCatalog(MemoryCatalog):
            def product_type_coefficient(self, product_type_id):
                raise AssertionError("в справочник ушел нецелый id")

        calculator = MaterialCalculator(
            StrictCatalog(COEFFICIENTS, DEFECT_PERCENTS))
        result = calculator.calculate_material("1 OR 1=1", MATERIAL_1,
                                               250, 2.5, 1.2)
        self.assertEqual(result, ERROR_RESULT)


class TestProblemText(unittest.TestCase):
    """find_problem объясняет, почему расчет вернул -1."""

    def setUp(self):
        self.calculator = make_calculator()

    def test_each_error_has_its_own_explanation(self):
        cases = (((LAMINATE, MATERIAL_1, 0, 2.5, 1.2), QUANTITY_PROBLEM),
                 ((LAMINATE, MATERIAL_1, 250, -1, 1.2), PARAMETERS_PROBLEM),
                 ((99, MATERIAL_1, 250, 2.5, 1.2), PRODUCT_TYPE_PROBLEM),
                 ((LAMINATE, 99, 250, 2.5, 1.2), MATERIAL_TYPE_PROBLEM))
        for arguments, problem in cases:
            with self.subTest(arguments=arguments):
                self.assertEqual(self.calculator.find_problem(*arguments),
                                 problem)

    def test_correct_data_has_no_problem(self):
        self.assertIsNone(self.calculator.find_problem(
            LAMINATE, MATERIAL_1, 250, 2.5, 1.2))

    def test_explanation_tells_what_to_do(self):
        for problem in (QUANTITY_PROBLEM, PARAMETERS_PROBLEM,
                        PRODUCT_TYPE_PROBLEM, MATERIAL_TYPE_PROBLEM):
            with self.subTest(problem=problem):
                self.assertIn("Пожалуйста", problem)


class OneRowCursor:
    """Курсор-заглушка: запоминает запрос и отдает одну строку."""

    def __init__(self, row):
        self.row = row
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    def execute(self, query, parameters=None):
        self.queries.append((query, parameters))

    def fetchone(self):
        return self.row


class OneRowConnection:
    """Соединение-заглушка с одним курсором."""

    def __init__(self, row):
        self.recorded = OneRowCursor(row)

    def cursor(self):
        return self.recorded


class TestDatabaseCatalog(unittest.TestCase):
    """Справочник из базы: запрос по id с параметром."""

    def test_coefficient_is_read_by_id_parameter(self):
        connection = OneRowConnection((Decimal("2.35"),))
        catalog = DatabaseCatalog(connection)
        self.assertEqual(catalog.product_type_coefficient(1), Decimal("2.35"))
        query, parameters = connection.recorded.queries[0]
        self.assertIn("WHERE id = %s", query)
        self.assertEqual(parameters, (1,))

    def test_missing_type_gives_none(self):
        catalog = DatabaseCatalog(OneRowConnection(None))
        self.assertIsNone(catalog.material_defect_percent(99))

    def test_type_lists_become_dictionaries(self):
        class ListCursor(OneRowCursor):
            description = (("id",), ("name",), ("value",))

            def fetchall(self):
                return [(1, "Ламинат", Decimal("2.35"))]

        class ListConnection:
            def cursor(self):
                return ListCursor(None)

        expected = [{"id": 1, "name": "Ламинат", "value": Decimal("2.35")}]
        self.assertEqual(get_product_types(ListConnection()), expected)
        self.assertEqual(get_material_types(ListConnection()), expected)

    def test_calculation_with_database_catalog(self):
        class TwoValueConnection:
            def cursor(self):
                return OneRowCursor((Decimal("1"),))

        calculator = MaterialCalculator(DatabaseCatalog(TwoValueConnection()))
        self.assertEqual(calculator.calculate_material(1, 1, 1, 3, 1), 4)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
