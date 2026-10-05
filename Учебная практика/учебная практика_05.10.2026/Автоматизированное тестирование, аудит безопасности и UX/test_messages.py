"""Тесты сообщений об ошибках: у каждого есть пошаговое руководство."""

import re
import unittest

from psycopg2 import Error as DatabaseError
from psycopg2 import IntegrityError, OperationalError

import material_calculator
import validation
from main_window import UNEXPECTED_MESSAGE
from material_calculator_window import UNKNOWN_PROBLEM
from messages import (FIX_HEADER, SCHEMA_STEP, SERVICE_STEP,
                      database_message, instructions)
from partner_edit_window import DUPLICATE_MESSAGES, constraint_message

STEP = re.compile(r"^\d+\. \S", re.M)

ERROR_TEXTS = {
    "количество продукции": material_calculator.QUANTITY_PROBLEM,
    "параметры продукции": material_calculator.PARAMETERS_PROBLEM,
    "тип продукции": material_calculator.PRODUCT_TYPE_PROBLEM,
    "тип материала": material_calculator.MATERIAL_TYPE_PROBLEM,
    "рейтинг": validation.RATING_MESSAGE,
    "ИНН": validation.INN_MESSAGE,
    "email": validation.EMAIL_MESSAGE,
    "повтор ИНН": DUPLICATE_MESSAGES["partners_inn_uk"],
    "повтор email": DUPLICATE_MESSAGES["partners_email_uk"],
    "другое ограничение": constraint_message(IntegrityError("check")),
    "расчет без причины": UNKNOWN_PROBLEM,
    "непредвиденная ошибка": UNEXPECTED_MESSAGE,
    "нет связи с базой": database_message(
        "Не удалось сохранить карточку", OperationalError("timeout"),
        "Нажмите «Сохранить» еще раз."),
    "база ответила ошибкой": database_message(
        "Не удалось загрузить список партнеров",
        DatabaseError("column does not exist"), "Нажмите «Обновить»."),
}


def validation_text(**changes) -> str:
    """Текст ошибки проверки карточки с испорченным полем."""
    values = {"name": "Вектор", "partner_type": "ООО", "director": "",
              "rating": "5", "phone": "", "email": "vector@mail.ru",
              "inn": "7701234567", "legal_address": ""}
    values.update(changes)
    try:
        validation.checked_values(values)
    except validation.ValidationError as error:
        return str(error)
    raise AssertionError("данные неожиданно прошли проверку")


class TestInstructions(unittest.TestCase):
    """Общий вид сообщения: суть проблемы, затем шаги по порядку."""

    def test_steps_are_numbered_after_header(self):
        text = instructions("Что-то пошло не так.", "Сделайте раз.",
                            "Сделайте два.")
        self.assertEqual(text, "Что-то пошло не так.\n\nКак исправить:\n"
                               "1. Сделайте раз.\n2. Сделайте два.")

    def test_lost_connection_points_to_service(self):
        self.assertIn(SERVICE_STEP, ERROR_TEXTS["нет связи с базой"])

    def test_other_database_error_points_to_schema(self):
        self.assertIn(SCHEMA_STEP, ERROR_TEXTS["база ответила ошибкой"])
        self.assertNotIn("нет связи", ERROR_TEXTS["база ответила ошибкой"])

    def test_reason_from_database_is_shown(self):
        self.assertIn("Причина: column does not exist",
                      ERROR_TEXTS["база ответила ошибкой"])


class TestEveryErrorHasGuide(unittest.TestCase):
    """Ни одно окно ошибки не оставляет менеджера без порядка действий."""

    def test_fixed_texts(self):
        for case, text in ERROR_TEXTS.items():
            with self.subTest(case=case):
                self.assertIn(f"\n\n{FIX_HEADER}\n", text)
                self.assertGreaterEqual(len(STEP.findall(text)), 2)

    def test_texts_built_while_checking_card(self):
        cases = {"пустое наименование": {"name": ""},
                 "пустой ИНН": {"inn": ""},
                 "длинный телефон": {"phone": "+7 900 000 00 00 доб. 1234"}}
        for case, changes in cases.items():
            with self.subTest(case=case):
                text = validation_text(**changes)
                self.assertGreaterEqual(len(STEP.findall(text)), 2)

    def test_empty_field_guide_names_the_field(self):
        self.assertIn("1. Перейдите в поле «ИНН».",
                      validation_text(inn=""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
