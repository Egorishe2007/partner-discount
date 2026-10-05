"""Тесты формы карточки: поля из ТЗ, подсказки и заполнение из реестра."""

import unittest

from app_test_base import PARTNERS, WindowTestCase
from form_fields import Tooltip
from partner_edit_window import EMAIL_HINT, PARTNER_TYPES, PHONE_HINT

FORM_FIELDS = {"name", "partner_type", "director", "rating",
               "phone", "email", "inn", "legal_address"}


class TestPartnerForm(WindowTestCase):
    """Карточка партнера без реальной базы: данные берутся из заглушки."""

    def test_form_has_every_field_from_specification(self):
        editor = self.navigator.open_editor()
        self.assertEqual(set(editor.fields), FORM_FIELDS)

    def test_partner_type_is_a_dropdown_list(self):
        type_box = self.navigator.open_editor().fields["partner_type"]
        self.assertEqual(str(type_box.cget("state")), "readonly")
        self.assertEqual(tuple(type_box.cget("values")), PARTNER_TYPES)

    def test_new_partner_starts_with_zero_rating(self):
        editor = self.navigator.open_editor()
        self.assertEqual(editor.values()["rating"], "0")

    def test_hints_are_shown_but_not_counted_as_data(self):
        editor = self.navigator.open_editor()
        self.assertEqual(editor.fields["phone"].get(), PHONE_HINT)
        self.assertEqual(editor.fields["email"].get(), EMAIL_HINT)
        self.assertEqual(editor.values()["phone"], "")
        self.assertEqual(editor.values()["email"], "")

    def test_typing_replaces_the_hint(self):
        phone = self.navigator.open_editor().fields["phone"]
        phone.hide_hint()
        phone.insert(0, "+7 900 000 00 09")
        self.assertEqual(phone.get_value(), "+7 900 000 00 09")

    def test_edit_mode_fills_fields_from_registry(self):
        editor = self.navigator.open_editor(PARTNERS[1])
        values = editor.values()
        self.assertEqual(values["name"], "Большой Склад")
        self.assertEqual(values["partner_type"], "ОАО")
        self.assertEqual(values["email"], "zakaz@sklad.example")
        self.assertEqual(values["inn"], "7100000005")
        self.assertEqual(values["rating"], "10")

    def test_partner_id_is_kept_outside_the_form(self):
        editor = self.navigator.open_editor(PARTNERS[1])
        self.assertEqual(editor.partner_id, 2)
        self.assertNotIn("id", editor.fields)

    def test_tooltip_appears_and_disappears(self):
        editor = self.navigator.open_editor()
        tooltip = Tooltip(editor.fields["phone"], "подсказка")
        tooltip.show()
        self.assertTrue(tooltip.window.winfo_exists())
        tooltip.hide()
        self.assertIsNone(tooltip.window)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
