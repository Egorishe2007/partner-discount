"""Тесты проверки данных карточки: что именно не пускается в базу."""

import unittest

from validation import ValidationError, checked_rating, checked_values

CORRECT = {
    "name": "Альфа-Строй",
    "partner_type": "ООО",
    "director": "Зайцев Артем Олегович",
    "rating": "6",
    "phone": "+7 900 000 00 07",
    "email": "office@alfa-stroy.example",
    "inn": "7700000007",
    "legal_address": "г. Москва, ул. Полевая, д. 4",
}


def without(field, value=""):
    """Те же данные, но с испорченным или пустым полем."""
    return dict(CORRECT, **{field: value})


class TestCheckedValues(unittest.TestCase):
    """Проверка полей карточки перед отправкой в базу."""

    def test_correct_card_passes(self):
        values = checked_values(dict(CORRECT))
        self.assertEqual(values["name"], "Альфа-Строй")

    def test_rating_becomes_a_number(self):
        self.assertEqual(checked_values(dict(CORRECT))["rating"], 6)

    def test_spaces_around_values_are_removed(self):
        values = checked_values(without("name", "  Альфа-Строй  "))
        self.assertEqual(values["name"], "Альфа-Строй")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError) as error:
            checked_values(without("name"))
        self.assertIn("Наименование", str(error.exception))

    def test_empty_email_is_rejected(self):
        with self.assertRaises(ValidationError) as error:
            checked_values(without("email"))
        self.assertIn("Электронная почта", str(error.exception))

    def test_email_without_at_sign_is_rejected(self):
        with self.assertRaises(ValidationError):
            checked_values(without("email", "office.alfa-stroy.example"))

    def test_empty_required_field_is_rejected(self):
        for field in ("director", "phone", "inn", "legal_address"):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    checked_values(without(field))

    def test_message_tells_what_to_do(self):
        with self.assertRaises(ValidationError) as error:
            checked_values(without("name"))
        self.assertIn("Пожалуйста", str(error.exception))


class TestCheckedRating(unittest.TestCase):
    """Рейтинг: целое неотрицательное число и ничего больше."""

    def test_zero_is_allowed(self):
        self.assertEqual(checked_rating("0"), 0)

    def test_number_with_spaces_is_allowed(self):
        self.assertEqual(checked_rating(" 7 "), 7)

    def test_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            checked_rating("пять")

    def test_punctuation_is_rejected(self):
        with self.assertRaises(ValidationError):
            checked_rating("7.5")

    def test_negative_number_is_rejected(self):
        with self.assertRaises(ValidationError):
            checked_rating("-1")

    def test_empty_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            checked_rating("")


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
