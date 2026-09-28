"""Тесты навигации: окна приложения, переходы между ними и заголовки."""

import unittest

from app_test_base import PARTNERS, WindowTestCase
from partner_edit_window import ADD_TITLE, EDIT_TITLE


class TestNavigation(WindowTestCase):
    """Переходы «реестр → другое окно → реестр» без реальной базы."""

    def test_registry_has_own_window_title(self):
        self.assertEqual(self.registry.title(), "CRM: Реестр партнеров")

    def test_add_button_opens_card_in_add_mode(self):
        editor = self.navigator.open_editor()
        self.assertEqual(editor.title(), ADD_TITLE)
        self.assertIsNone(editor.partner)

    def test_double_click_opens_card_in_edit_mode(self):
        self.registry.edit_partner(PARTNERS[1])
        editor = self.navigator.child
        self.assertEqual(editor.title(), EDIT_TITLE)
        self.assertEqual(editor.partner["id"], 2)

    def test_registry_hides_while_other_window_is_open(self):
        self.navigator.open_editor()
        self.registry.update()
        self.assertEqual(self.registry.state(), "withdrawn")

    def test_back_closes_window_and_shows_registry(self):
        editor = self.navigator.open_editor()
        editor.go_back()
        self.registry.update()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(self.registry.state(), "normal")

    def test_registry_keeps_partners_after_return(self):
        cards_before = len(self.registry.cards.body.winfo_children())
        self.navigator.open_editor(PARTNERS[0]).go_back()
        self.assertEqual(self.registry.partners, PARTNERS)
        self.assertEqual(len(self.registry.cards.body.winfo_children()),
                         cards_before)

    def test_second_call_does_not_open_another_window(self):
        first = self.navigator.open_editor()
        second = self.navigator.open_history(2)
        self.assertIs(first, second)

    def test_window_close_button_returns_to_registry(self):
        editor = self.navigator.open_editor()
        self.assertNotEqual(editor.protocol("WM_DELETE_WINDOW"), "")


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
