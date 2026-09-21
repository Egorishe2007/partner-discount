"""Второе окно приложения: карточка добавления и редактирования."""

import tkinter as tk
from tkinter import ttk

import app_resources
import ui_style

ADD_TITLE = "CRM: Карточка партнера [Добавление]"
EDIT_TITLE = "CRM: Карточка партнера [Редактирование]"
ADD_MODE = "Режим: добавление нового партнера"
EDIT_MODE = "Режим: редактирование партнера"


class PartnerEditWindow(tk.Toplevel):
    """Карточка партнера: открывается вместо реестра.

    Окно работает в двух режимах. Партнер передан из реестра —
    режим редактирования, партнер не передан (None) — добавление
    нового. От режима зависит заголовок окна, поэтому по подписи в
    панели задач всегда видно, что именно сейчас открыто.
    """

    def __init__(self, master, navigator, partner: dict = None):
        super().__init__(master, background=ui_style.BACKGROUND)
        self.navigator = navigator
        self.partner = partner
        self.title(EDIT_TITLE if partner else ADD_TITLE)
        self.geometry("760x520")
        self.minsize(640, 420)
        app_resources.set_window_icon(self)
        # Крестик окна и Esc ведут туда же, куда кнопка «Назад»:
        # иначе реестр остался бы скрытым, а приложение — без окон.
        self.protocol("WM_DELETE_WINDOW", self.go_back)
        self.bind("<Escape>", self.go_back)
        self.build_header()
        self.build_body()
        self.build_footer()

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
                f'«{self.partner["name"]}», запись № {self.partner["id"]}')

    def build_body(self):
        """Рабочая область карточки."""
        body = tk.Frame(self,
                        background=ui_style.BACKGROUND,
                        highlightbackground=ui_style.BORDER,
                        highlightcolor=ui_style.BORDER,
                        highlightthickness=1)
        body.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(body,
                 text=self.body_text(),
                 justify="left",
                 font=ui_style.CARD_TEXT_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="nw",
                                                      padx=18, pady=18)

    def body_text(self) -> str:
        """Что показать в рабочей области на этом этапе проекта."""
        if self.partner is None:
            return ("Реестр передал пустую карточку: партнер создается\n"
                    "с нуля.\n\n"
                    "Поля карточки верстаются в задании «Разработка формы\n"
                    "добавления/редактирования партнера».")
        return (f'Реестр передал в карточку партнера № '
                f'{self.partner["id"]}:\n\n'
                f'Наименование: {self.partner["name"]}\n'
                f'Директор: {self.partner["director"]}\n'
                f'Телефон: {self.partner["phone"]}\n'
                f'Рейтинг: {self.partner["rating"]}\n'
                f'Скидка: {self.partner["discount_percent"]}%\n\n'
                "Поля карточки верстаются в задании «Разработка формы\n"
                "добавления/редактирования партнера».")

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
