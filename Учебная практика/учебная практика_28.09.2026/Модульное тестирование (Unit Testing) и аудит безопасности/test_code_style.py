"""Проверка кода на правила из ТЗ: одна команда на строку и snake_case."""

import ast
import io
import os
import re
import tokenize
import unittest

FOLDER = os.path.dirname(os.path.abspath(__file__))
SNAKE_CASE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*$")
CONSTANT_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
CAMEL_CASE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
# Эти имена задает сам unittest, переименовать их нельзя.
UNITTEST_NAMES = {"setUp", "tearDown"}


def python_files() -> list:
    """Все модули проекта в папке задания."""
    return sorted(name for name in os.listdir(FOLDER)
                  if name.endswith(".py"))


def read_source(name: str) -> str:
    """Текст модуля."""
    with open(os.path.join(FOLDER, name), encoding="utf-8") as source:
        return source.read()


def shared_lines(source: str) -> list:
    """Номера строк, где начинается больше одной команды.

    Так ловятся и «a = 1; b = 2», и «if x: return y»: у условия и у
    команды внутри него одна и та же строка начала.
    """
    seen = set()
    repeated = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.stmt):
            continue
        if node.lineno in seen:
            repeated.append(node.lineno)
        seen.add(node.lineno)
    return sorted(repeated)


def semicolon_lines(source: str) -> list:
    """Строки с точкой с запятой вне строковых литералов."""
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return [token.start[0] for token in tokens
            if token.type == tokenize.OP and token.string == ";"]


def badly_named(source: str) -> list:
    """Имена, которые нарушают snake_case и CamelCase из ТЗ."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef):
            allowed = (SNAKE_CASE.match(node.name)
                       or node.name in UNITTEST_NAMES)
            if not allowed:
                problems.append(node.name)
            for argument in node.args.args + node.args.kwonlyargs:
                if not SNAKE_CASE.match(argument.arg):
                    problems.append(argument.arg)
        elif isinstance(node, ast.ClassDef):
            if not CAMEL_CASE.match(node.name):
                problems.append(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            allowed = (SNAKE_CASE.match(node.id)
                       or CONSTANT_CASE.match(node.id))
            if not allowed:
                problems.append(node.id)
    return problems


class TestCodeStyle(unittest.TestCase):
    """Правила оформления кода проверяются по всем модулям папки."""

    def test_checker_finds_two_commands_on_one_line(self):
        self.assertEqual(shared_lines("a = 1; b = 2\n"), [1])
        self.assertEqual(shared_lines("if a:\n    b = 1\n"), [])
        self.assertEqual(shared_lines("if a: b = 1\n"), [1])

    def test_checker_finds_camel_case_function(self):
        self.assertEqual(badly_named("def calculateMaterial():\n    pass\n"),
                         ["calculateMaterial"])

    def test_one_command_per_line(self):
        for name in python_files():
            with self.subTest(module=name):
                self.assertEqual(shared_lines(read_source(name)), [])

    def test_no_semicolons(self):
        for name in python_files():
            with self.subTest(module=name):
                self.assertEqual(semicolon_lines(read_source(name)), [])

    def test_names_follow_snake_case(self):
        for name in python_files():
            with self.subTest(module=name):
                self.assertEqual(badly_named(read_source(name)), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
