"""Unit-тесты calculate_partner_discount: граничные значения из ТЗ."""

import unittest

from partner_discount import calculate_partner_discount


class TestCalculatePartnerDiscount(unittest.TestCase):

    def test_0_gives_0_percent(self):
        self.assertEqual(calculate_partner_discount(0), 0)

    def test_9999_gives_0_percent(self):
        self.assertEqual(calculate_partner_discount(9999), 0)

    def test_10000_gives_5_percent(self):
        self.assertEqual(calculate_partner_discount(10000), 5)

    def test_49999_gives_5_percent(self):
        self.assertEqual(calculate_partner_discount(49999), 5)

    def test_50000_gives_10_percent(self):
        self.assertEqual(calculate_partner_discount(50000), 10)

    def test_299999_gives_10_percent(self):
        self.assertEqual(calculate_partner_discount(299999), 10)

    def test_300000_gives_15_percent(self):
        self.assertEqual(calculate_partner_discount(300000), 15)

    def test_negative_quantity_raises_error(self):
        with self.assertRaises(ValueError):
            calculate_partner_discount(-1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
