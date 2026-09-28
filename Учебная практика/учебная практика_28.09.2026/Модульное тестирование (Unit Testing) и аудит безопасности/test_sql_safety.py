"""Аудит защиты от SQL-инъекций: данные уходят в запрос только параметрами.

Проверка идет по исходному коду всех модулей приложения: каждый
cursor.execute получает текст запроса константой, а значения — отдельным
аргументом. Сборка запроса из пользовательских данных через f-строку,
«+», «%» или .format() считается нарушением.
"""

import ast
import datetime
import os
import re
import unittest

from partner_service import (PARTNER_INSERT, SALES_HISTORY_QUERY,
                             get_sales_history, insert_partner)

FOLDER = os.path.dirname(os.path.abspath(__file__))
CONSTANT_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
INJECTION = "Партнер'); DROP TABLE partners; --"


def application_modules() -> list:
    """Модули приложения без тестов: именно они ходят в базу."""
    return sorted(name for name in os.listdir(FOLDER)
                  if name.endswith(".py") and not name.startswith("test_"))


def read_tree(name: str) -> ast.Module:
    """Разобранный код модуля."""
    with open(os.path.join(FOLDER, name), encoding="utf-8") as source:
        return ast.parse(source.read())


def is_safe_query(node) -> bool:
    """Текст запроса — строка в кавычках или константа модуля."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    return isinstance(node, ast.Name) and bool(CONSTANT_CASE.match(node.id))


def unsafe_execute_calls(tree: ast.Module) -> list:
    """Номера строк, где execute получает собранный на ходу запрос."""
    lines = []
    for node in ast.walk(tree):
        is_execute = (isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "execute")
        if is_execute and node.args and not is_safe_query(node.args[0]):
            lines.append(node.lineno)
    return lines


def unsafe_query_constants(tree: ast.Module) -> list:
    """Константы-запросы, в f-строку которых подставлено не константа.

    Запрос можно собрать из других констант SQL (так в partner_service
    общий список столбцов подставляется в два запроса), но переменная
    с данными в тексте запроса — это уже дыра.
    """
    names = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.JoinedStr):
            continue
        for part in node.value.values:
            has_data = (isinstance(part, ast.FormattedValue)
                        and not is_safe_query(part.value))
            if has_data:
                names.append(node.targets[0].id)
    return names


class RecordingCursor:
    """Курсор-заглушка: запоминает запрос и параметры отдельно."""

    description = (("product_name",), ("quantity",), ("sale_date",))

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

    def fetchone(self):
        return (7,)

    def fetchall(self):
        return [("Ламинат", 1, datetime.date(2025, 1, 1))]


class RecordingConnection:
    """Соединение-заглушка, которое ничего не выполняет по-настоящему."""

    def __init__(self):
        self.recorded = RecordingCursor()

    def cursor(self):
        return self.recorded

    def commit(self):
        pass


class TestAuditTool(unittest.TestCase):
    """Сначала убеждаемся, что проверка ловит опасный код."""

    def test_f_string_is_caught(self):
        tree = ast.parse('cursor.execute(f"SELECT * FROM partners '
                         'WHERE id = {partner_id}")')
        self.assertEqual(unsafe_execute_calls(tree), [1])

    def test_concatenation_and_formatting_are_caught(self):
        samples = ('cursor.execute("SELECT * FROM partners WHERE name = \'"'
                   ' + name + "\'")',
                   'cursor.execute("... WHERE id = %s" % partner_id)',
                   'cursor.execute("... WHERE id = {}".format(partner_id))')
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertEqual(unsafe_execute_calls(ast.parse(sample)), [1])

    def test_parameterized_call_passes(self):
        tree = ast.parse('cursor.execute("... WHERE id = %s", (user_id,))')
        self.assertEqual(unsafe_execute_calls(tree), [])

    def test_query_with_data_in_f_string_is_caught(self):
        tree = ast.parse('USER_QUERY = f"SELECT * FROM users WHERE id = '
                         '{user_id}"')
        self.assertEqual(unsafe_query_constants(tree), ["USER_QUERY"])


class TestApplicationCode(unittest.TestCase):
    """Все запросы приложения параметризованы."""

    def test_every_execute_gets_constant_query(self):
        for name in application_modules():
            with self.subTest(module=name):
                self.assertEqual(unsafe_execute_calls(read_tree(name)), [])

    def test_query_constants_contain_no_data(self):
        for name in application_modules():
            with self.subTest(module=name):
                self.assertEqual(unsafe_query_constants(read_tree(name)), [])


class TestInjectionAttempt(unittest.TestCase):
    """Текст атаки из поля формы остается просто данными."""

    def test_partner_name_goes_as_parameter(self):
        connection = RecordingConnection()
        values = {"name": INJECTION, "partner_type": "ООО",
                  "director": "Иванов Иван Иванович", "rating": 5,
                  "phone": "+7 900 000 00 01", "email": "a@b.example",
                  "inn": "7700000001", "legal_address": "г. Москва"}
        insert_partner(connection, values)
        self.assertEqual(connection.recorded.query, PARTNER_INSERT)
        self.assertNotIn("DROP", connection.recorded.query)
        self.assertEqual(connection.recorded.parameters["name"], INJECTION)

    def test_partner_id_goes_as_parameter(self):
        connection = RecordingConnection()
        get_sales_history(connection, "1 OR 1=1")
        self.assertEqual(connection.recorded.query, SALES_HISTORY_QUERY)
        self.assertEqual(connection.recorded.parameters, ("1 OR 1=1",))


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
