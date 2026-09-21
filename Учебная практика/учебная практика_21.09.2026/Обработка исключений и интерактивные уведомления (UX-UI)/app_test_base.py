"""Основа тестов окон: поддельные данные вместо PostgreSQL."""

import tkinter as tk
import unittest

import dialogs
import main_window
import partner_edit_window
from navigation import Navigator

PARTNERS = [
    {"id": 1, "partner_type": "ООО", "name": "СтройМастер",
     "director": "Иванов Иван Иванович", "email": "info@stroymaster.example",
     "phone": "+7 900 000 00 01", "legal_address": "г. Москва, д. 1",
     "inn": "7700000001", "rating": 7, "total_quantity": 9999,
     "discount_percent": 0},
    {"id": 2, "partner_type": "ОАО", "name": "Большой Склад",
     "director": "Смирнова Елена Андреевна", "email": "zakaz@sklad.example",
     "phone": "+7 900 000 00 05", "legal_address": "г. Тула, д. 3",
     "inn": "7100000005", "rating": 10, "total_quantity": 300000,
     "discount_percent": 15},
]


class FakeConnection:
    """Соединение-заглушка: окно закрывает его после выборки."""

    def close(self):
        pass


def partners_copy() -> list:
    """Свежие копии партнеров, чтобы тест не портил общий список."""
    return [dict(partner) for partner in PARTNERS]


def partner_by_id(partner_id):
    """Найти партнера в поддельной базе по его id."""
    for partner in PARTNERS:
        if partner["id"] == partner_id:
            return dict(partner)
    return None


def tk_is_available() -> bool:
    """Проверить, что окна можно создавать: нужен рабочий стол."""
    try:
        root = tk.Tk()
    except tk.TclError:
        return False
    root.destroy()
    return True


def patch_module(module, **functions) -> dict:
    """Подменить функции модуля и вернуть прежние значения."""
    saved = {name: getattr(module, name) for name in functions}
    for name, function in functions.items():
        setattr(module, name, function)
    return saved


def restore_module(module, saved: dict):
    """Вернуть модулю его настоящие функции."""
    for name, function in saved.items():
        setattr(module, name, function)


@unittest.skipUnless(tk_is_available(), "нет графической оболочки")
class WindowTestCase(unittest.TestCase):
    """Окна приложения, у которых вместо базы — заглушка.

    Настоящая база для тестов не нужна: окна читают данные через
    функции модуля, а тест подменяет их на время проверки.
    """

    def setUp(self):
        self.saved = {main_window: patch_module(
            main_window,
            get_connection=FakeConnection,
            get_partners_with_discounts=lambda connection: partners_copy())}
        # Карточка тоже ходит в базу: читает партнера по id при
        # открытии и пишет его при сохранении.
        self.saved[partner_edit_window] = patch_module(
            partner_edit_window,
            get_connection=FakeConnection,
            get_partner_with_discount=lambda connection, partner_id:
                partner_by_id(partner_id))
        # Диалоговые окна модальные, в тестах их не показываем:
        # запоминаем тип и текст, а ответ на предупреждение задает тест.
        self.dialogs = []
        self.warning_answer = True
        self.saved[dialogs] = patch_module(dialogs,
                                           show_error=self.record_error,
                                           show_warning=self.record_warning,
                                           show_info=self.record_info)
        self.navigator = Navigator()
        self.registry = self.navigator.main_window

    def record_error(self, parent, message):
        """Запомнить показанное окно ошибки."""
        self.dialogs.append(("error", message))

    def record_warning(self, parent, message):
        """Запомнить предупреждение и ответить так, как задал тест."""
        self.dialogs.append(("warning", message))
        return self.warning_answer

    def record_info(self, parent, message):
        """Запомнить уведомление об успешной операции."""
        self.dialogs.append(("info", message))

    def dialog_kinds(self) -> list:
        """Типы показанных диалоговых окон по порядку."""
        return [kind for kind, message in self.dialogs]

    def tearDown(self):
        self.registry.destroy()
        for module, saved in self.saved.items():
            restore_module(module, saved)
