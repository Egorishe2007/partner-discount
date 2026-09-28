"""Окно расчета материалов на партию продукции."""

import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import app_resources
import dialogs
import ui_style
from db import get_connection
from form_fields import ChoiceBox, HintEntry
from material_calculator import (ERROR_RESULT, DatabaseCatalog,
                                 MaterialCalculator, get_material_types,
                                 get_product_types)

WINDOW_TITLE = "CRM: Расчет материалов"
EMPTY_RESULT = "—"
READY_MESSAGE = "Заполните поля и нажмите «Рассчитать»."
FAILED_MESSAGE = "Расчет невозможен: исправьте данные и повторите."
UNKNOWN_PROBLEM = (
    "Расчет невозможен: данные не прошли проверку.\n\n"
    "Пожалуйста, проверьте все поля формы и повторите расчет.")
CATALOG_MESSAGE = (
    "Не удалось загрузить справочники типов продукции и материалов: "
    "база данных недоступна.\n\n"
    "Причина: {}\n\n"
    "Пожалуйста, проверьте, что сервер PostgreSQL запущен, вернитесь в "
    "реестр и откройте расчет еще раз.")
DATABASE_MESSAGE = (
    "Расчет не выполнен: база данных недоступна.\n\n"
    "Причина: {}\n\n"
    "Пожалуйста, проверьте, что сервер PostgreSQL запущен, и повторите "
    "расчет. Введенные данные останутся в форме.")


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для диалогового окна."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


def parse_whole(text: str):
    """Целое число из поля ввода; если не число — текст как есть.

    Проверку окно не дублирует: получив не число, метод расчета вернет
    -1, и менеджер увидит ту же понятную причину, что и для остальных
    ошибок ввода.
    """
    try:
        return int(text.strip())
    except ValueError:
        return text


def parse_number(text: str):
    """Дробное число из поля; запятая и точка как разделитель равны."""
    try:
        return float(text.strip().replace(",", "."))
    except ValueError:
        return text


def format_decimal(value) -> str:
    """Дробь с запятой, как принято в русском тексте: 2.35 → 2,35."""
    return str(value).replace(".", ",")


def format_amount(amount: int) -> str:
    """Количество с пробелами между разрядами: 1765 → 1 765."""
    return f"{amount:,}".replace(",", " ")


class MaterialCalculatorWindow(tk.Toplevel):
    """Калькулятор сырья: форма входных данных и результат расчета.

    Значения справочников для выпадающих списков загружаются при
    открытии, а сам расчет каждый раз обращается к базе: если тип
    удалили, пока окно было открыто, метод вернет -1, а не старые
    данные.
    """

    def __init__(self, master, navigator):
        super().__init__(master, background=ui_style.BACKGROUND)
        self.navigator = navigator
        self.product_types = []
        self.material_types = []
        self.fields = {}
        self.logo_image = None
        self.title(WINDOW_TITLE)
        self.geometry("820x680")
        self.minsize(720, 640)
        app_resources.set_window_icon(self)
        # Крестик окна и Esc ведут туда же, куда кнопка «Назад»: иначе
        # реестр остался бы скрытым, а приложение — без окон.
        self.protocol("WM_DELETE_WINDOW", self.go_back)
        self.bind("<Escape>", self.go_back)
        self.bind("<Return>", self.calculate)
        error = self.load_catalog()
        self.build_header()
        self.build_status_bar()
        self.build_footer()
        self.build_form()
        self.build_result()
        self.show_status(READY_MESSAGE)
        if error is not None:
            dialogs.show_error(self, CATALOG_MESSAGE.format(error))

    def load_catalog(self):
        """Прочитать справочники; вернуть текст ошибки базы или None."""
        try:
            with closing(get_connection()) as connection:
                self.product_types = get_product_types(connection)
                self.material_types = get_material_types(connection)
        except DatabaseError as error:
            return first_line(error)
        return None

    def build_header(self):
        """Шапка: логотип компании и назначение окна."""
        header = tk.Frame(self, background=ui_style.BACKGROUND)
        header.pack(fill="x", side="top")
        self.logo_image = app_resources.load_logo()
        if self.logo_image is not None:
            tk.Label(header,
                     image=self.logo_image,
                     background=ui_style.BACKGROUND).pack(side="left",
                                                          padx=(24, 0),
                                                          pady=16)
        titles = tk.Frame(header, background=ui_style.BACKGROUND)
        titles.pack(side="left", padx=16, pady=20)
        tk.Label(titles,
                 text="Расчет материалов",
                 font=ui_style.TITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.TEXT).pack(anchor="w")
        tk.Label(titles,
                 text="Сколько сырья нужно на партию продукции с учетом брака",
                 font=ui_style.SUBTITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w")
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="top")

    def build_form(self):
        """Поля ввода: типы из справочников, количество и параметры."""
        form = tk.Frame(self,
                        background=ui_style.BACKGROUND,
                        highlightbackground=ui_style.BORDER,
                        highlightcolor=ui_style.BORDER,
                        highlightthickness=1)
        form.pack(fill="x", padx=24, pady=(20, 0))
        form.columnconfigure(0, weight=1, uniform="field")
        form.columnconfigure(1, weight=1, uniform="field")
        product_choices = [
            (row["id"], f'{row["name"]} — коэффициент '
                        f'{format_decimal(row["coefficient"])}')
            for row in self.product_types]
        material_choices = [
            (row["id"], f'{row["name"]} — брак '
                        f'{format_decimal(row["defect_percent"])} %')
            for row in self.material_types]
        self.add_field(form, 0, 0, "product_type", "Тип продукции",
                       ChoiceBox, choices=product_choices)
        self.add_field(form, 0, 1, "material_type", "Тип материала",
                       ChoiceBox, choices=material_choices)
        self.add_field(form, 1, 0, "quantity", "Количество продукции, шт.",
                       HintEntry, hint="например, 250")
        self.add_field(form, 2, 0, "param_1", "Параметр продукции 1",
                       HintEntry, hint="например, 2,5")
        self.add_field(form, 2, 1, "param_2", "Параметр продукции 2",
                       HintEntry, hint="например, 1,2")
        tk.Frame(form,
                 background=ui_style.BACKGROUND,
                 height=14).grid(row=3, column=0, columnspan=2)

    def add_field(self, form, row, column, key, caption, widget_class,
                  **options):
        """Поставить в сетку подпись и поле ввода под ней."""
        box = tk.Frame(form, background=ui_style.BACKGROUND)
        box.grid(row=row, column=column, sticky="ew",
                 padx=18, pady=(14, 0))
        tk.Label(box,
                 text=caption,
                 font=ui_style.FIELD_LABEL_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w",
                                                      pady=(0, 4))
        widget = widget_class(box, **options)
        widget.pack(fill="x")
        self.fields[key] = widget

    def build_result(self):
        """Панель результата: итог крупно и данные, по которым он получен."""
        panel = tk.Frame(self,
                         background=ui_style.BACKGROUND,
                         highlightbackground=ui_style.BORDER,
                         highlightcolor=ui_style.BORDER,
                         highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(panel,
                 text="Потребуется материала",
                 font=ui_style.FIELD_LABEL_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w",
                                                      padx=18, pady=(14, 0))
        self.result_label = tk.Label(panel,
                                     text=EMPTY_RESULT,
                                     font=ui_style.RESULT_FONT,
                                     background=ui_style.BACKGROUND,
                                     foreground=ui_style.TEXT)
        self.result_label.pack(anchor="w", padx=18)
        self.details_label = tk.Label(panel,
                                      text=READY_MESSAGE,
                                      justify="left",
                                      wraplength=700,
                                      font=ui_style.CARD_TEXT_FONT,
                                      background=ui_style.BACKGROUND,
                                      foreground=ui_style.MUTED_TEXT)
        self.details_label.pack(anchor="w", padx=18, pady=(0, 14))

    def build_status_bar(self):
        """Строка состояния внизу окна."""
        self.status = tk.Label(self,
                               anchor="w",
                               font=ui_style.STATUS_FONT,
                               background=ui_style.BACKGROUND,
                               foreground=ui_style.MUTED_TEXT,
                               padx=24,
                               pady=10)
        self.status.pack(fill="x", side="bottom")
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")

    def show_status(self, message: str):
        """Написать сообщение в строке состояния."""
        self.status.configure(text=message)

    def build_footer(self):
        """Нижняя панель: расчет и возврат в реестр."""
        footer = tk.Frame(self, background=ui_style.BACKGROUND)
        footer.pack(fill="x", side="bottom")
        ttk.Button(footer,
                   text="Рассчитать",
                   style="Primary.TButton",
                   command=self.calculate).pack(side="right", padx=(0, 24),
                                                pady=16)
        ttk.Button(footer,
                   text="Назад",
                   style="Card.TButton",
                   command=self.go_back).pack(side="right", padx=(0, 10),
                                              pady=16)
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")

    def arguments(self) -> tuple:
        """Данные формы в том порядке, в каком их ждет метод расчета."""
        return (self.fields["product_type"].get_value(),
                self.fields["material_type"].get_value(),
                parse_whole(self.fields["quantity"].get_value()),
                parse_number(self.fields["param_1"].get_value()),
                parse_number(self.fields["param_2"].get_value()))

    def calculate(self, event=None):
        """Посчитать материал по данным формы и показать результат."""
        arguments = self.arguments()
        try:
            with closing(get_connection()) as connection:
                calculator = MaterialCalculator(DatabaseCatalog(connection))
                result = calculator.calculate_material(*arguments)
                problem = None
                if result == ERROR_RESULT:
                    problem = calculator.find_problem(*arguments)
        except DatabaseError as error:
            self.show_failure("Расчет не выполнен: база данных недоступна.")
            dialogs.show_error(self, DATABASE_MESSAGE.format(
                first_line(error)))
            return
        # -1 — не число материала, а сигнал «данные неверны»: вместо
        # него показываем причину, которую объяснил сам калькулятор.
        if result == ERROR_RESULT:
            self.show_failure(FAILED_MESSAGE)
            dialogs.show_error(self, problem or UNKNOWN_PROBLEM)
            return
        self.show_success(result)

    def show_success(self, result: int):
        """Показать итог расчета и данные, по которым он получен."""
        quantity = self.fields["quantity"].get_value()
        param_1 = self.fields["param_1"].get_value()
        param_2 = self.fields["param_2"].get_value()
        self.result_label.configure(text=format_amount(result),
                                    foreground=ui_style.TEXT)
        self.details_label.configure(
            text=(f'{self.fields["product_type"].get()}\n'
                  f'{self.fields["material_type"].get()}\n'
                  f"Партия {quantity} шт., параметры {param_1} × {param_2}"))
        self.show_status("Расчет выполнен.")

    def show_failure(self, message: str):
        """Убрать прежний итог, чтобы он не выглядел как новый."""
        self.result_label.configure(text=EMPTY_RESULT,
                                    foreground=ui_style.HINT_TEXT)
        self.details_label.configure(text=message)
        self.show_status(message)

    def go_back(self, event=None):
        """Закрыть расчет и вернуться на главную форму."""
        self.navigator.back_to_main()
