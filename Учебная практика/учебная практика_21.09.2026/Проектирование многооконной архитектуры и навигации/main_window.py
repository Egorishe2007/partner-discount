"""Главная форма CRM: реестр партнеров с рассчитанными скидками."""

import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import app_resources
import ui_style
from db import get_connection
from partner_cards import CardList
from partner_service import get_partners_with_discounts

WINDOW_TITLE = "CRM: Реестр партнеров"
WINDOW_SUBTITLE = "Объемы продаж и рассчитанные скидки партнеров"


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для строки состояния."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


class MainWindow(tk.Tk):
    """Главное окно приложения: шапка, реестр партнеров, состояние.

    Окно создается один раз за запуск: на время работы с карточкой
    партнера навигатор его прячет, а не уничтожает, поэтому при
    возврате список остается загруженным.
    """

    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self.partners = []
        self.logo_image = None
        self.title(WINDOW_TITLE)
        self.geometry("900x660")
        self.minsize(760, 480)
        self.configure(background=ui_style.BACKGROUND)
        ui_style.apply_theme(self)
        app_resources.set_window_icon(self)
        self.build_header()
        self.build_status_bar()
        self.cards = CardList(self, self.edit_partner)
        self.cards.pack(fill="both", expand=True, padx=24, pady=20)
        self.load_partners()

    def build_header(self):
        """Шапка: логотип, заголовок и кнопки действий."""
        header = tk.Frame(self, background=ui_style.BACKGROUND)
        header.pack(fill="x", side="top")
        self.place_logo(header)
        titles = tk.Frame(header, background=ui_style.BACKGROUND)
        titles.pack(side="left", padx=16, pady=20)
        tk.Label(titles,
                 text=WINDOW_TITLE,
                 font=ui_style.TITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.TEXT).pack(anchor="w")
        tk.Label(titles,
                 text=WINDOW_SUBTITLE,
                 font=ui_style.SUBTITLE_FONT,
                 background=ui_style.BACKGROUND,
                 foreground=ui_style.MUTED_TEXT).pack(anchor="w")
        self.add_button = ttk.Button(header,
                                     text="Добавить партнера",
                                     style="Primary.TButton",
                                     command=self.add_partner)
        self.add_button.pack(side="right", padx=(0, 24))
        ttk.Button(header,
                   text="Обновить",
                   style="Card.TButton",
                   command=self.load_partners).pack(side="right", padx=(0, 10))
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="top")

    def place_logo(self, header):
        """Показать логотип компании из папки ресурсов."""
        self.logo_image = app_resources.load_logo()
        if self.logo_image is None:
            return
        tk.Label(header,
                 image=self.logo_image,
                 background=ui_style.BACKGROUND).pack(side="left",
                                                      padx=(24, 0),
                                                      pady=16)

    def build_status_bar(self):
        """Строка состояния внизу окна."""
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")
        self.status = tk.Label(self,
                               anchor="w",
                               font=ui_style.STATUS_FONT,
                               background=ui_style.BACKGROUND,
                               foreground=ui_style.MUTED_TEXT,
                               padx=24,
                               pady=10)
        self.status.pack(fill="x", side="bottom")

    def show_status(self, message: str):
        """Написать сообщение в строке состояния."""
        self.status.configure(text=message)

    def load_partners(self):
        """Перечитать партнеров из базы данных и показать карточки."""
        self.show_status("Загрузка данных...")
        self.update_idletasks()
        try:
            with closing(get_connection()) as connection:
                self.partners = get_partners_with_discounts(connection)
        except DatabaseError as error:
            self.partners = []
            self.cards.clear()
            self.show_status(f"Нет связи с базой данных: {first_line(error)}")
            return
        self.cards.show_partners(self.partners)
        self.show_status(f"Партнеров загружено: {len(self.partners)}. "
                         "Нажмите на карточку, чтобы открыть ее.")

    def add_partner(self):
        """Перейти к карточке нового партнера."""
        self.navigator.open_editor()

    def edit_partner(self, partner: dict):
        """Перейти к карточке выбранного партнера."""
        self.navigator.open_editor(partner)

    def on_return(self):
        """Сообщить, что реестр снова на экране и список сохранен."""
        self.show_status(f"Вы вернулись в реестр. "
                         f"Партнеров в списке: {len(self.partners)}.")
