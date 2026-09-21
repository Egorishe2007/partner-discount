"""Второе окно приложения: форма добавления и редактирования партнера."""

import tkinter as tk
from tkinter import ttk

import app_resources
import ui_style
from form_fields import HintEntry, RatingBox, Tooltip, TypeBox

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


class PartnerEditWindow(tk.Toplevel):
    """Карточка партнера: открывается вместо реестра.

    Окно работает в двух режимах. Партнер передан из реестра — режим
    редактирования, партнер не передан (None) — добавление нового. От
    режима зависит заголовок окна и заполнение полей.
    """

    def __init__(self, master, navigator, partner: dict = None):
        super().__init__(master, background=ui_style.BACKGROUND)
        self.navigator = navigator
        self.partner = partner
        # id партнера нужен отдельно от полей формы: на форме его не
        # показываем и не даем править, но именно по нему запись потом
        # обновляется в базе.
        self.partner_id = partner["id"] if partner else None
        self.fields = {}
        self.title(EDIT_TITLE if partner else ADD_TITLE)
        self.geometry("820x600")
        self.minsize(720, 560)
        app_resources.set_window_icon(self)
        # Крестик окна и Esc ведут туда же, куда кнопка «Назад»: иначе
        # реестр остался бы скрытым, а приложение — без окон.
        self.protocol("WM_DELETE_WINDOW", self.go_back)
        self.bind("<Escape>", self.go_back)
        self.build_header()
        self.build_footer()
        self.build_form()
        self.fill_form()

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
        """Заполнить поля данными партнера, если он передан из реестра."""
        if self.partner is None:
            return
        for key, widget in self.fields.items():
            widget.set_value(self.partner.get(key))

    def values(self) -> dict:
        """Собрать введенные значения полей карточки."""
        return {key: widget.get_value()
                for key, widget in self.fields.items()}

    def build_footer(self):
        """Нижняя панель: режим работы и кнопка возврата."""
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")
        footer = tk.Frame(self, background=ui_style.BACKGROUND)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer,
                 text=EDIT_MODE if self.partner else ADD_MODE,
                 font=ui_style.STATUS_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(side="left",
                                                      padx=24, pady=16)
        ttk.Button(footer,
                   text="Назад",
                   style="Primary.TButton",
                   command=self.go_back).pack(side="right", padx=24, pady=16)

    def go_back(self, event=None):
        """Закрыть карточку и вернуться на главную форму."""
        self.navigator.back_to_main()
