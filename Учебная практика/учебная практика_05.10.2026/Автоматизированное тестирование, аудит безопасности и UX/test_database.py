"""Проверка ядра на настоящей базе после импорта (schema.sql, import.sql).

Если PostgreSQL недоступен, тесты пропускаются: остальные проверки
работают без базы. Тесты только читают данные и ничего не меняют.
"""

import datetime
import unittest
from decimal import Decimal

from psycopg2 import Error as DatabaseError

from db import get_connection
from material_calculator import DatabaseCatalog, MaterialCalculator
from partner_service import (get_partner_discount,
                             get_partners_with_discounts, get_sales_history,
                             search_partners_with_discounts)


def open_database():
    """Подключение к базе или None, если она недоступна."""
    try:
        return get_connection()
    except DatabaseError:
        return None


class TestImportedDatabase(unittest.TestCase):
    """Скидки, история и расчет сырья по данным заказчика."""

    @classmethod
    def setUpClass(cls):
        cls.connection = open_database()
        if cls.connection is None:
            raise unittest.SkipTest("база данных недоступна")

    @classmethod
    def tearDownClass(cls):
        cls.connection.rollback()
        cls.connection.close()

    def test_all_imported_partners_get_discount(self):
        partners = get_partners_with_discounts(self.connection)
        self.assertEqual(len(partners), 5)
        self.assertEqual({partner["discount_percent"] for partner in partners},
                         {0})

    def test_sales_volume_comes_from_database(self):
        partners = get_partners_with_discounts(self.connection)
        volumes = {partner["name"]: partner["total_quantity"]
                   for partner in partners}
        self.assertEqual(volumes["Альфа"], 10)
        self.assertEqual(volumes["Вектор"], 2)

    def test_unknown_partner_has_no_discount(self):
        self.assertIsNone(get_partner_discount(self.connection, 999))

    def test_history_joins_product_names(self):
        sales = get_sales_history(self.connection, 1)
        self.assertEqual(sales, [{"product_name": "Ноутбук Pro",
                                  "quantity": 2,
                                  "sale_date": datetime.date(2023, 10, 25),
                                  "amount": Decimal("150000.00")}])

    def test_materials_use_catalog_from_database(self):
        calculator = MaterialCalculator(DatabaseCatalog(self.connection))
        self.assertEqual(calculator.calculate_material(1, 1, 250, 2.5, 1.2),
                         1765)

    def test_unknown_types_in_database_give_minus_one(self):
        calculator = MaterialCalculator(DatabaseCatalog(self.connection))
        self.assertEqual(calculator.calculate_material(99, 1, 250, 2.5, 1.2),
                         -1)
        self.assertEqual(calculator.calculate_material(1, 99, 250, 2.5, 1.2),
                         -1)


    def test_search_by_legal_form(self):
        found = search_partners_with_discounts(self.connection, "ип")
        self.assertEqual(sorted(partner["name"] for partner in found),
                         ["Петров А.В.", "Сидоров И.И."])

    def test_search_by_part_of_inn(self):
        found = search_partners_with_discounts(self.connection, "770123")
        self.assertEqual([partner["name"] for partner in found], ["Вектор"])

    def test_percent_sign_is_not_a_wildcard(self):
        self.assertEqual(search_partners_with_discounts(self.connection, "%"),
                         [])

    def test_injection_finds_nothing_and_breaks_nothing(self):
        found = search_partners_with_discounts(
            self.connection, "'; DROP TABLE partners; --")
        self.assertEqual(found, [])
        self.assertEqual(len(get_partners_with_discounts(self.connection)), 5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
