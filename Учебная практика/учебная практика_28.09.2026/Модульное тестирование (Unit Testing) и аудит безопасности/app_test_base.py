"""Основа тестов окон: поддельные данные вместо PostgreSQL."""

import datetime
import tkinter as tk
import unittest
from decimal import Decimal

import dialogs
import main_window
import material_calculator_window
import partner_edit_window
import partner_history_window
from material_calculator import MemoryCatalog
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
    {"id": 3, "partner_type": "ООО", "name": "Новый Партнер",
     "director": "Васильев Дмитрий Игоревич",
     "email": "hello@new-partner.example", "phone": "+7 900 000 00 06",
     "legal_address": "г. Омск, д. 1", "inn": "5500000006", "rating": 3,
     "total_quantity": 0, "discount_percent": 0},
]

SALES = {
    1: [{"product_name": "Ламинат Дуб дымчато-белый 33 класс 12 мм",
         "quantity": 4999, "sale_date": datetime.date(2025, 6, 10)},
        {"product_name": "Паркетная доска Ясень темный однополосная 14 мм",
         "quantity": 5000, "sale_date": datetime.date(2025, 3, 15)}],
    2: [{"product_name": "Ламинат Дуб дымчато-белый 33 класс 12 мм",
         "quantity": 150000, "sale_date": datetime.date(2026, 3, 14)},
        {"product_name": "Паркетная доска Ясень темный однополосная 14 мм",
         "quantity": 150000, "sale_date": datetime.date(2025, 7, 7)}],
}


PRODUCT_TYPES = [
    {"id": 1, "name": "Ламинат", "coefficient": Decimal("2.35")},
    {"id": 3, "name": "Паркетная доска", "coefficient": Decimal("4.34")},
]
MATERIAL_TYPES = [
    {"id": 1, "name": "Тип материала 1", "defect_percent": Decimal("0.10")},
    {"id": 2, "name": "Тип материала 2", "defect_percent": Decimal("0.95")},
]


def catalog_of(product_types, material_types) -> MemoryCatalog:
    """Мок-справочник из тех же строк, что видит окно расчета."""
    return MemoryCatalog(
        {row["id"]: row["coefficient"] for row in product_types},
        {row["id"]: row["defect_percent"] for row in material_types})


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


def sales_of(partner_id) -> list:
    """Продажи партнера из поддельной базы."""
    return [dict(sale) for sale in SALES.get(partner_id, [])]


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
        self.saved[partner_edit_window] = patch_module(
            partner_edit_window,
            get_connection=FakeConnection,
            get_partner_with_discount=lambda connection, partner_id:
                partner_by_id(partner_id))
        self.saved[partner_history_window] = patch_module(
            partner_history_window,
            get_connection=FakeConnection,
            get_partner_with_discount=lambda connection, partner_id:
                partner_by_id(partner_id),
            get_sales_history=lambda connection, partner_id:
                sales_of(partner_id))
        self.saved[material_calculator_window] = patch_module(
            material_calculator_window,
            get_connection=FakeConnection,
            get_product_types=lambda connection: list(PRODUCT_TYPES),
            get_material_types=lambda connection: list(MATERIAL_TYPES),
            DatabaseCatalog=lambda connection:
                catalog_of(PRODUCT_TYPES, MATERIAL_TYPES))
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
