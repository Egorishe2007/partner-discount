"""Тесты сохранения карточки: INSERT, UPDATE и обновление реестра."""

import unittest

from psycopg2 import Error as DatabaseError

import main_window
import partner_edit_window
from app_test_base import (PARTNERS, WindowTestCase, partners_copy,
                           patch_module)
from partner_service import insert_partner, update_partner

NEW_PARTNER = {
    "name": "Новый Партнер",
    "partner_type": "ИП",
    "director": "Васильев Дмитрий Игоревич",
    "rating": 4,
    "phone": "+7 900 000 00 09",
    "email": "hello@new-partner.example",
    "inn": "5500000006",
    "legal_address": "г. Омск, ул. Новая, д. 1",
}


class RecordingCursor:
    """Курсор-заглушка: запоминает запрос и его параметры."""

    def __init__(self, rowcount=1, new_id=7):
        self.queries = []
        self.parameters = []
        self.rowcount = rowcount
        self.new_id = new_id

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    def execute(self, query, parameters=None):
        self.queries.append(query)
        self.parameters.append(parameters)

    def fetchone(self):
        return (self.new_id,)


class RecordingConnection:
    """Соединение-заглушка со счетчиком подтверждений транзакции."""

    def __init__(self, rowcount=1, new_id=7):
        self.recorded = RecordingCursor(rowcount, new_id)
        self.commits = 0

    def cursor(self):
        return self.recorded

    def commit(self):
        self.commits += 1

    def close(self):
        pass


class TestPartnerQueries(unittest.TestCase):
    """Запросы записи данных на поддельном соединении."""

    def test_insert_returns_id_of_new_row(self):
        connection = RecordingConnection(new_id=7)
        self.assertEqual(insert_partner(connection, dict(NEW_PARTNER)), 7)

    def test_insert_sends_every_field_of_the_card(self):
        connection = RecordingConnection()
        insert_partner(connection, dict(NEW_PARTNER))
        self.assertEqual(connection.recorded.parameters[0], NEW_PARTNER)

    def test_insert_is_committed(self):
        connection = RecordingConnection()
        insert_partner(connection, dict(NEW_PARTNER))
        self.assertEqual(connection.commits, 1)

    def test_update_goes_by_primary_key(self):
        connection = RecordingConnection()
        self.assertTrue(update_partner(connection, 2, dict(NEW_PARTNER)))
        self.assertIn("WHERE id", connection.recorded.queries[0])
        self.assertEqual(connection.recorded.parameters[0]["id"], 2)

    def test_update_reports_missing_row(self):
        connection = RecordingConnection(rowcount=0)
        self.assertFalse(update_partner(connection, 99, dict(NEW_PARTNER)))


class TestCardSaving(WindowTestCase):
    """Сохранение карточки из окна: режимы добавления и изменения."""

    def setUp(self):
        super().setUp()
        self.inserted = []
        self.updated = []
        self.loads = []
        self.saved[partner_edit_window].update(patch_module(
            partner_edit_window,
            insert_partner=self.fake_insert,
            update_partner=self.fake_update))
        # Реестр уже загружен в setUp базового класса, поэтому счетчик
        # считает только повторные чтения — после сохранения.
        patch_module(main_window,
                     get_partners_with_discounts=self.counting_list)

    def fake_insert(self, connection, values):
        """Запомнить добавленную запись и вернуть ее номер."""
        self.inserted.append(values)
        return 7

    def fake_update(self, connection, partner_id, values):
        """Запомнить изменение записи."""
        self.updated.append((partner_id, values))
        return True

    def counting_list(self, connection):
        """Посчитать, сколько раз реестр перечитывал базу."""
        self.loads.append(1)
        return partners_copy()

    def fill(self, editor, **values):
        """Ввести значения в поля карточки."""
        for key, value in values.items():
            editor.fields[key].set_value(value)

    def test_new_partner_goes_to_database(self):
        editor = self.navigator.open_editor()
        self.fill(editor, **NEW_PARTNER)
        editor.save()
        self.assertEqual(len(self.inserted), 1)
        self.assertEqual(self.inserted[0]["name"], "Новый Партнер")
        self.assertEqual(self.updated, [])

    def test_rating_goes_to_database_as_a_number(self):
        editor = self.navigator.open_editor()
        self.fill(editor, **NEW_PARTNER)
        editor.save()
        self.assertEqual(self.inserted[0]["rating"], 4)

    def test_saved_card_closes_and_registry_reloads(self):
        editor = self.navigator.open_editor()
        self.fill(editor, **NEW_PARTNER)
        editor.save()
        self.registry.update()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(self.registry.state(), "normal")
        self.assertEqual(len(self.loads), 1)

    def test_existing_partner_is_updated_by_id(self):
        editor = self.navigator.open_editor(PARTNERS[1])
        self.fill(editor, name="Большой Склад плюс")
        editor.save()
        partner_id, values = self.updated[0]
        self.assertEqual(partner_id, 2)
        self.assertEqual(values["name"], "Большой Склад плюс")
        self.assertEqual(self.inserted, [])

    def test_card_loads_fresh_data_by_id(self):
        stale = dict(PARTNERS[1], name="Старое название")
        editor = self.navigator.open_editor(stale)
        self.assertEqual(editor.values()["name"], "Большой Склад")

    def test_deleted_partner_is_saved_as_a_new_row(self):
        patch_module(partner_edit_window,
                     update_partner=lambda connection, partner_id, values:
                     False)
        editor = self.navigator.open_editor(PARTNERS[1])
        editor.save()
        self.assertEqual(len(self.inserted), 1)

    def test_card_stays_open_if_rating_is_not_a_number(self):
        editor = self.navigator.open_editor()
        self.fill(editor, **NEW_PARTNER)
        editor.fields["rating"].set_value("пять")
        editor.save()
        self.assertTrue(editor.winfo_exists())
        self.assertEqual(self.inserted, [])

    def test_card_stays_open_if_database_is_unavailable(self):
        def failing_insert(connection, values):
            raise DatabaseError("нет связи с базой данных")

        patch_module(partner_edit_window, insert_partner=failing_insert)
        editor = self.navigator.open_editor()
        self.fill(editor, **NEW_PARTNER)
        editor.save()
        self.assertTrue(editor.winfo_exists())
        self.assertEqual(self.loads, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
