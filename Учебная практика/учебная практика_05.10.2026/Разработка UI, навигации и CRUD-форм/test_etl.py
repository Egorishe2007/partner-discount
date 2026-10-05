"""Тесты очистки данных: каждая аномалия из файлов заказчика."""

import csv
import os
import shutil
import tempfile
import unittest
from decimal import Decimal

import etl
from etl import (RejectedRow, clean_count, clean_date, clean_email,
                 clean_inn, clean_money, clean_partner_name, read_csv,
                 run_etl, squeeze_spaces)


class TestTextCleaning(unittest.TestCase):
    """Пробелы, кавычки, лишние точки и латиница в названиях."""

    def test_spaces_are_trimmed_and_squeezed(self):
        self.assertEqual(squeeze_spaces("  Петров   А.В. "), "Петров А.В.")

    def test_legal_form_is_split_from_name(self):
        self.assertEqual(clean_partner_name(' ООО "Вектор" '),
                         ("ООО", "Вектор"))

    def test_loose_dots_and_latin_initials_are_fixed(self):
        self.assertEqual(clean_partner_name("ИП ...Петров  A.B."),
                         ("ИП", "Петров А.В."))

    def test_latin_words_outside_initials_stay(self):
        self.assertEqual(clean_partner_name('ООО "Pro Market"'),
                         ("ООО", "Pro Market"))

    def test_name_without_legal_form_is_rejected(self):
        with self.assertRaises(RejectedRow):
            clean_partner_name("Вектор")

    def test_email_is_trimmed_and_lowercased(self):
        self.assertEqual(clean_email("  Alpha@Gmail.com "), "alpha@gmail.com")

    def test_broken_email_is_rejected(self):
        with self.assertRaises(RejectedRow):
            clean_email("alpha@gmail")

    def test_inn_has_ten_or_twelve_digits(self):
        self.assertEqual(clean_inn(" 7701234567 "), "7701234567")
        self.assertEqual(clean_inn("770123456789"), "770123456789")
        with self.assertRaises(RejectedRow):
            clean_inn("77012345")


class TestDates(unittest.TestCase):
    """Все форматы дат из файла приводятся к ГГГГ-ММ-ДД."""

    def test_every_format_from_file(self):
        cases = {"25.10.2023": "2023-10-25", "2023/10/26": "2023-10-26",
                 "2023-10-27": "2023-10-27", "28-10-2023": "2023-10-28",
                 "2023.10.29": "2023-10-29", " 2023-10-30 ": "2023-10-30"}
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean_date(raw), expected)

    def test_impossible_date_is_rejected(self):
        with self.assertRaises(RejectedRow):
            clean_date("31.02.2023")

    def test_text_instead_of_date_is_rejected(self):
        with self.assertRaises(RejectedRow):
            clean_date("вчера")


class TestNumbers(unittest.TestCase):
    """Деньги — Decimal с копейками, количество и id — целые больше 0."""

    def test_money_gets_two_decimal_places(self):
        self.assertEqual(clean_money("45000.5"), Decimal("45000.50"))
        self.assertEqual(clean_money("18200,0"), Decimal("18200.00"))

    def test_bad_money_is_rejected(self):
        for raw in ("abc", "-5", "NaN"):
            with self.subTest(raw=raw):
                with self.assertRaises(RejectedRow):
                    clean_money(raw)

    def test_count_must_be_positive_integer(self):
        self.assertEqual(clean_count(" 10 "), 10)
        for raw in ("0", "-1", "2.5", ""):
            with self.subTest(raw=raw):
                with self.assertRaises(RejectedRow):
                    clean_count(raw)


class TestReading(unittest.TestCase):
    """Кодировка и кавычки внутри значений."""

    def test_windows_1251_file_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "products.csv")
            with open(path, "w", encoding="cp1251", newline="") as source:
                source.write('product_id,product_name,price\r\n'
                             '103,Монитор 27",18200.0\r\n')
            encoding, header, rows = read_csv(path)
        self.assertEqual(encoding, "cp1251")
        self.assertEqual(rows, [(2, ["103", 'Монитор 27"', "18200.0"])])


class TestWholeRun(unittest.TestCase):
    """Полный прогон на настоящих файлах заказчика во временной папке."""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.mkdtemp()
        for name in (etl.PARTNERS_SOURCE, etl.PRODUCTS_SOURCE,
                     etl.SALES_SOURCE):
            shutil.copy(os.path.join(etl.DATA_DIR, name), cls.folder)
        cls.report = run_etl(cls.folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def read_output(self, name) -> list:
        """Строки записанного CSV без заголовка."""
        with open(os.path.join(self.folder, name), encoding="utf-8",
                  newline="") as target:
            return list(csv.reader(target))[1:]

    def test_partners_are_clean(self):
        self.assertEqual(self.read_output(etl.PARTNERS_TARGET), [
            ["1", "ООО", "Вектор", "7701234567", "vector@mail.ru"],
            ["2", "ИП", "Петров А.В.", "7802345678", "petrov@yandex.ru"],
            ["3", "АО", "Технолоджис", "5003456789", "info@techno.ru"],
            ["4", "ООО", "Альфа", "7704567890", "alpha@gmail.com"],
            ["5", "ИП", "Сидоров И.И.", "7805678901", "sidorov@llc.ru"]])

    def test_products_are_clean(self):
        self.assertEqual(self.read_output(etl.PRODUCTS_TARGET), [
            ["101", "Ноутбук Pro", "75000.00"],
            ["102", "Смартфон X", "45000.50"],
            ["103", 'Монитор 27"', "18200.00"]])

    def test_sale_with_unknown_partner_is_removed(self):
        sale_ids = [row[0] for row in self.read_output(etl.SALES_TARGET)]
        self.assertEqual(sale_ids, ["1001", "1002", "1004", "1005", "1006"])
        rejected = self.read_output(etl.REJECTED_TARGET)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0][2], "партнер 999 не найден")

    def test_all_dates_are_iso(self):
        dates = [row[3] for row in self.read_output(etl.SALES_TARGET)]
        self.assertEqual(dates, ["2023-10-25", "2023-10-26", "2023-10-28",
                                 "2023-10-29", "2023-10-30"])

    def test_amounts_match_price_times_quantity(self):
        self.assertEqual(self.report.amount_mismatches, [])

    def test_encodings_are_reported(self):
        self.assertEqual(self.report.encodings[etl.PRODUCTS_SOURCE],
                         "cp1251")
        self.assertEqual(self.report.encodings[etl.PARTNERS_SOURCE], "utf-8")

    def test_every_fix_is_logged(self):
        fields = {row[2] for row in self.read_output(etl.LOG_TARGET)}
        self.assertEqual(fields, {"partner_name", "email", "product_name",
                                  "sale_date"})


class TestDuplicates(unittest.TestCase):
    """Повтор ИНН или email нарушил бы UNIQUE — строка отклоняется."""

    def test_second_partner_with_same_inn_is_rejected(self):
        report = etl.EtlReport()
        rows = [(2, ["1", "ООО Вектор", "7701234567", "a@b.ru"]),
                (3, ["2", "ООО Альфа", "7701234567", "c@d.ru"])]
        partners = etl.clean_partners(rows, report)
        self.assertEqual([partner[0] for partner in partners], [1])
        self.assertEqual(len(report.rejected), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
