"""Тесты partner_service на поддельном соединении, без реальной базы."""

import unittest

from partner_service import (get_partner_with_discount,
                             get_partners_with_discounts)

PARTNER_COLUMNS = (
    ("id",),
    ("partner_type",),
    ("name",),
    ("director",),
    ("email",),
    ("phone",),
    ("rating",),
    ("total_quantity",),
)


def make_row(total_quantity):
    """Собрать строку результата запроса с заданным объемом продаж."""
    return (1, "ООО", "СтройМастер", "Иванов Иван Иванович",
            "info@stroymaster.example", "+7 900 000 00 01", 7,
            total_quantity)


class FakeCursor:
    """Курсор-заглушка: отдает заранее заданные строки вместо запроса."""

    def __init__(self, rows):
        self.rows = rows
        self.description = PARTNER_COLUMNS
        self.query = None

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    def execute(self, query, parameters=None):
        self.query = query

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows[0]

    def fetchall(self):
        return self.rows


class FakeConnection:
    """Соединение-заглушка, выдающее FakeCursor с нужными строками."""

    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return FakeCursor(self.rows)


class TestPartnerService(unittest.TestCase):

    def test_partner_with_sales_gets_discount(self):
        connection = FakeConnection([make_row(50000)])
        partner = get_partner_with_discount(connection, 1)
        self.assertEqual(partner["discount_percent"], 10)

    def test_partner_without_sales_history_gets_zero(self):
        connection = FakeConnection([make_row(None)])
        partner = get_partner_with_discount(connection, 1)
        self.assertEqual(partner["total_quantity"], 0)
        self.assertEqual(partner["discount_percent"], 0)

    def test_zero_quantity_gets_zero_discount(self):
        connection = FakeConnection([make_row(0)])
        partner = get_partner_with_discount(connection, 1)
        self.assertEqual(partner["discount_percent"], 0)

    def test_unknown_partner_returns_none(self):
        connection = FakeConnection([])
        self.assertIsNone(get_partner_with_discount(connection, 999))

    def test_partners_list_gets_discounts(self):
        rows = [make_row(9999), make_row(300000), make_row(None)]
        partners = get_partners_with_discounts(FakeConnection(rows))
        discounts = [partner["discount_percent"] for partner in partners]
        self.assertEqual(discounts, [0, 15, 0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
