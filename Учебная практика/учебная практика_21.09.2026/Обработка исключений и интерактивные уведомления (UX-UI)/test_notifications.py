"""Тесты уведомлений: когда окно показывает ошибку, предупреждение и успех."""

import unittest

from psycopg2 import Error as DatabaseError

import main_window
import partner_edit_window
from app_test_base import PARTNERS, WindowTestCase, patch_module
from dialogs import ERROR_TITLE, INFO_TITLE, WARNING_TITLE

NEW_PARTNER = {
    "name": "Альфа-Строй",
    "partner_type": "ООО",
    "director": "Зайцев Артем Олегович",
    "rating": 6,
    "phone": "+7 900 000 00 07",
    "email": "office@alfa-stroy.example",
    "inn": "7700000007",
    "legal_address": "г. Москва, ул. Полевая, д. 4",
}


class TestNotifications(WindowTestCase):
    """Диалоговые окна вместо аварийных завершений."""

    def setUp(self):
        super().setUp()
        self.inserted = []
        self.saved[partner_edit_window].update(patch_module(
            partner_edit_window,
            insert_partner=self.fake_insert,
            update_partner=lambda connection, partner_id, values: True))

    def fake_insert(self, connection, values):
        """Запомнить добавленную запись и вернуть ее номер."""
        self.inserted.append(values)
        return 7

    def new_card(self, **changes):
        """Открыть карточку нового партнера и заполнить ее."""
        editor = self.navigator.open_editor()
        for key, value in dict(NEW_PARTNER, **changes).items():
            editor.fields[key].set_value(value)
        return editor

    def test_dialog_titles_say_what_happened(self):
        self.assertEqual(ERROR_TITLE, "CRM: Ошибка")
        self.assertEqual(WARNING_TITLE, "CRM: Предупреждение")
        self.assertEqual(INFO_TITLE, "CRM: Уведомление")

    def test_error_when_rating_is_not_a_number(self):
        editor = self.new_card(rating="пять")
        editor.save()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIn("Рейтинг", self.dialogs[0][1])
        self.assertIn("Пожалуйста", self.dialogs[0][1])
        self.assertEqual(self.inserted, [])
        self.assertTrue(editor.winfo_exists())

    def test_error_when_rating_is_negative(self):
        self.new_card(rating="-3").save()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertEqual(self.inserted, [])

    def test_error_when_name_is_empty(self):
        self.new_card(name="").save()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIn("Наименование", self.dialogs[0][1])

    def test_error_when_email_is_empty(self):
        self.new_card(email="").save()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIn("Электронная почта", self.dialogs[0][1])

    def test_error_when_database_is_unavailable(self):
        def failing_insert(connection, values):
            raise DatabaseError("could not connect to server")

        patch_module(partner_edit_window, insert_partner=failing_insert)
        editor = self.new_card()
        editor.save()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertIn("PostgreSQL", self.dialogs[0][1])
        self.assertTrue(editor.winfo_exists())

    def test_registry_reports_unavailable_database(self):
        def failing_connection():
            raise DatabaseError("could not connect to server")

        patch_module(main_window, get_connection=failing_connection)
        self.registry.load_partners()
        self.assertEqual(self.dialog_kinds(), ["error"])
        self.assertEqual(self.registry.partners, [])

    def test_information_after_saving(self):
        editor = self.new_card()
        editor.save()
        self.registry.update()
        self.assertEqual(self.dialog_kinds(), ["info"])
        self.assertIn("Альфа-Строй", self.dialogs[0][1])
        self.assertFalse(editor.winfo_exists())

    def test_warning_before_losing_changes(self):
        self.warning_answer = False
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.fields["name"].set_value("Другое название")
        editor.go_back()
        self.assertEqual(self.dialog_kinds(), ["warning"])
        self.assertIn("потеряны", self.dialogs[0][1])
        self.assertTrue(editor.winfo_exists())

    def test_confirmed_warning_returns_to_registry(self):
        self.warning_answer = True
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.fields["rating"].set_value(3)
        editor.go_back()
        self.registry.update()
        self.assertEqual(self.dialog_kinds(), ["warning"])
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(self.registry.state(), "normal")

    def test_no_warning_when_nothing_was_changed(self):
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.go_back()
        self.assertEqual(self.dialogs, [])
        self.assertFalse(editor.winfo_exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
