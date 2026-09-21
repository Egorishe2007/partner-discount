"""Второе окно приложения: форма добавления и редактирования партнера."""

import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import app_resources
import dialogs
import ui_style
from db import get_connection
from form_fields import HintEntry, RatingBox, Tooltip, TypeBox
from partner_service import (get_partner_with_discount, insert_partner,
                             update_partner)
from validation import ValidationError, checked_values

ADD_TITLE = "CRM: Карточка партнера [Добавление]"
EDIT_TITLE = "CRM: Карточка партнера [Редактирование]"
ADD_MODE = "Режим: добавление нового партнера"
EDIT_MODE = "Режим: редактирование партнера"

PARTNER_TYPES = ("ЗАО", "ООО", "ИП", "ОАО", "ПАО")
PHONE_HINT = "+7 900 000 00 00"
EMAIL_HINT = "partner@example.com"
INN_HINT = "10 или 12 цифр"
PHONE_TOOLTIP = "Телефон с кодом страны, например +7 900 000 00 00"
EMAIL_TOOLTIP = "Рабочая почта компании, например partner@example.com"

NEW_PARTNER_MESSAGE = "Заполните карточку и нажмите «Сохранить»."
LOADED_MESSAGE = "Данные партнера загружены из базы."
GONE_MESSAGE = ("Записи уже нет в базе: партнера удалили. "
                "Сохранение добавит его заново.")
LOSS_WARNING = (
    "В карточке есть изменения, которых еще нет в базе.\n\n"
    "Если выйти сейчас, они будут потеряны безвозвратно: вернуть их "
    "будет нельзя.\n\nВыйти без сохранения?")
DATABASE_MESSAGE = (
    "Не удалось сохранить карточку: база данных недоступна.\n\n"
    "Причина: {}\n\n"
    "Пожалуйста, проверьте, что сервер PostgreSQL запущен и переменная "
    "DB_PASSWORD задана верно, затем повторите сохранение. Введенные "
    "данные останутся в карточке.")


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для строки состояния."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


class PartnerEditWindow(tk.Toplevel):
    """Карточка партнера: открывается вместо реестра.

    Окно работает в двух режимах. Партнер передан из реестра — режим
    редактирования, партнер не передан (None) — добавление нового. От
    режима зависит заголовок окна, заполнение полей и то, каким
    запросом карточка сохраняется: INSERT или UPDATE.
    """

    def __init__(self, master, navigator, partner: dict = None):
        super().__init__(master, background=ui_style.BACKGROUND)
        self.navigator = navigator
        self.partner = partner
        # id партнера нужен отдельно от полей формы: на форме его не
        # показываем и не даем править, но именно по нему запись
        # читается и обновляется в базе.
        self.partner_id = partner["id"] if partner else None
        self.fields = {}
        self.title(EDIT_TITLE if partner else ADD_TITLE)
        self.geometry("820x640")
        self.minsize(720, 600)
        app_resources.set_window_icon(self)
        # Крестик окна и Esc ведут туда же, куда кнопка «Назад»: иначе
        # реестр остался бы скрытым, а приложение — без окон.
        self.protocol("WM_DELETE_WINDOW", self.go_back)
        self.bind("<Escape>", self.go_back)
        message = self.load_partner()
        self.build_header()
        self.build_status_bar()
        self.build_footer()
        self.build_form()
        self.fill_form()
        # Снимок значений: по нему видно, правил ли менеджер карточку,
        # и нужно ли предупреждать о потере данных при выходе.
        self.saved_values = self.values()
        self.show_status(message)

    def load_partner(self) -> str:
        """Перечитать партнера из базы по id и вернуть сообщение.

        Реестр мог быть загружен давно, поэтому карточка не доверяет
        копии данных из списка, а берет актуальную запись по первичному
        ключу. Если база недоступна, остаются данные из реестра.
        """
        if self.partner_id is None:
            return NEW_PARTNER_MESSAGE
        try:
            with closing(get_connection()) as connection:
                fresh = get_partner_with_discount(connection,
                                                  self.partner_id)
        except DatabaseError as error:
            return (f"Нет связи с базой данных: {first_line(error)}. "
                    "Показаны данные из реестра.")
        if fresh is None:
            return GONE_MESSAGE
        self.partner = fresh
        return LOADED_MESSAGE

    def build_header(self):
        """Шапка карточки: назначение окна и выбранный партнер."""
        header = tk.Frame(self, background=ui_style.BACKGROUND)
        header.pack(fill="x", side="top")
        titles = tk.Frame(header, background=ui_style.BACKGROUND)
        titles.pack(side="left", padx=24, pady=20)
        tk.Label(titles,
                 text="Карточка партнера",
                 font=ui_style.TITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.TEXT).pack(anchor="w")
        tk.Label(titles,
                 text=self.subtitle(),
                 font=ui_style.SUBTITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w")
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="top")

    def subtitle(self) -> str:
        """Подзаголовок: какой партнер открыт или что он новый."""
        if self.partner is None:
            return "Новый партнер еще не сохранен в базе данных"
        return (f'{self.partner["partner_type"]} '
                f'«{self.partner["name"]}», запись № {self.partner_id}')

    def build_form(self):
        """Поля карточки по списку из технического задания."""
        form = tk.Frame(self,
                        background=ui_style.BACKGROUND,
                        highlightbackground=ui_style.BORDER,
                        highlightcolor=ui_style.BORDER,
                        highlightthickness=1)
        form.pack(fill="both", expand=True, padx=24, pady=20)
        form.columnconfigure(0, weight=1, uniform="field")
        form.columnconfigure(1, weight=1, uniform="field")
        self.add_field(form, 0, 0, "name", "Наименование",
                       HintEntry, hint="Паркет-Сервис")
        self.add_field(form, 0, 1, "partner_type", "Тип партнера",
                       TypeBox, values=PARTNER_TYPES)
        self.add_field(form, 1, 0, "director", "ФИО директора",
                       HintEntry, hint="Иванов Иван Иванович")
        self.add_field(form, 1, 1, "rating", "Рейтинг", RatingBox)
        self.add_field(form, 2, 0, "phone", "Телефон",
                       HintEntry, hint=PHONE_HINT)
        self.add_field(form, 2, 1, "email", "Электронная почта",
                       HintEntry, hint=EMAIL_HINT)
        self.add_field(form, 3, 0, "inn", "ИНН", HintEntry, hint=INN_HINT)
        self.add_field(form, 4, 0, "legal_address", "Юридический адрес",
                       HintEntry, hint="г. Казань, ул. Лесная, д. 5",
                       columnspan=2)
        # Формат телефона и почты подсказываем еще и всплывающим
        # пояснением: серый плейсхолдер пропадает при первом же вводе.
        Tooltip(self.fields["phone"], PHONE_TOOLTIP)
        Tooltip(self.fields["email"], EMAIL_TOOLTIP)

    def add_field(self, form, row, column, key, caption, widget_class,
                  columnspan=1, **options):
        """Поставить в сетку подпись и поле ввода под ней."""
        box = tk.Frame(form, background=ui_style.BACKGROUND)
        box.grid(row=row, column=column, columnspan=columnspan,
                 sticky="ew", padx=18, pady=(14, 0))
        tk.Label(box,
                 text=caption,
                 font=ui_style.FIELD_LABEL_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w",
                                                      pady=(0, 4))
        widget = widget_class(box, **options)
        widget.pack(fill="x")
        self.fields[key] = widget

    def fill_form(self):
        """Заполнить поля данными партнера, если он открыт из реестра."""
        if self.partner is None:
            return
        for key, widget in self.fields.items():
            widget.set_value(self.partner.get(key))

    def values(self) -> dict:
        """Собрать введенные значения полей карточки."""
        return {key: widget.get_value()
                for key, widget in self.fields.items()}

    def has_changes(self) -> bool:
        """Отличается ли содержимое полей от загруженного в карточку."""
        return self.values() != self.saved_values

    def build_status_bar(self):
        """Строка состояния внизу карточки."""
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
        """Написать сообщение в строке состояния карточки."""
        self.status.configure(text=message)

    def build_footer(self):
        """Нижняя панель: режим работы, сохранение и возврат."""
        footer = tk.Frame(self, background=ui_style.BACKGROUND)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer,
                 text=EDIT_MODE if self.partner_id else ADD_MODE,
                 font=ui_style.STATUS_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(side="left",
                                                      padx=24, pady=16)
        ttk.Button(footer,
                   text="Сохранить",
                   style="Primary.TButton",
                   command=self.save).pack(side="right", padx=(0, 24),
                                           pady=16)
        ttk.Button(footer,
                   text="Назад",
                   style="Card.TButton",
                   command=self.go_back).pack(side="right", padx=(0, 10),
                                              pady=16)
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")

    def save(self):
        """Проверить данные, записать карточку и вернуться в реестр."""
        try:
            values = checked_values(self.values())
        except ValidationError as error:
            self.show_status("Данные не прошли проверку.")
            dialogs.show_error(self, str(error))
            return
        self.show_status("Сохранение...")
        self.update_idletasks()
        try:
            with closing(get_connection()) as connection:
                saved = self.write_partner(connection, values)
        except DatabaseError as error:
            self.show_status("Сохранить не удалось: база недоступна.")
            dialogs.show_error(self,
                               DATABASE_MESSAGE.format(first_line(error)))
            return
        dialogs.show_info(self, saved)
        self.navigator.back_to_main(reload=True)
        self.navigator.main_window.show_status(saved)

    def write_partner(self, connection, values: dict) -> str:
        """Выполнить INSERT или UPDATE и вернуть текст о результате."""
        if self.partner_id is None:
            self.partner_id = insert_partner(connection, values)
            return (f'Партнер «{values["name"]}» добавлен, '
                    f'запись № {self.partner_id}.')
        # Партнера могли удалить, пока карточка была открыта: тогда
        # UPDATE не находит строку, и запись создается заново, чтобы
        # введенные данные не пропали.
        if update_partner(connection, self.partner_id, values):
            return (f'Партнер «{values["name"]}» обновлен, '
                    f'запись № {self.partner_id}.')
        self.partner_id = insert_partner(connection, values)
        return (f'Записи уже не было в базе, партнер «{values["name"]}» '
                f'добавлен заново, запись № {self.partner_id}.')

    def go_back(self, event=None):
        """Вернуться в реестр, предупредив о несохраненных изменениях."""
        if self.has_changes() and not dialogs.show_warning(self,
                                                           LOSS_WARNING):
            return
        self.navigator.back_to_main()
