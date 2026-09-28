"""Главная форма CRM: реестр партнеров с рассчитанными скидками."""

import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import app_resources
import dialogs
import ui_style
from db import get_connection
from partner_cards import CardList
from partner_service import get_partners_with_discounts

WINDOW_TITLE = "CRM: Реестр партнеров"
WINDOW_SUBTITLE = "Объемы продаж и рассчитанные скидки партнеров"
NOTHING_SELECTED = "Партнер не выбран — щелкните по карточке в списке"
DATABASE_MESSAGE = (
    "Не удалось получить список партнеров: база данных недоступна.\n\n"
    "Причина: {}\n\n"
    "Пожалуйста, проверьте, что сервер PostgreSQL запущен и база "
    "partners_db создана, затем нажмите «Обновить».")


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для строки состояния."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


class MainWindow(tk.Tk):
    """Главное окно приложения: шапка, реестр партнеров, состояние.

    Окно создается один раз за запуск: на время работы с другими окнами
    навигатор его прячет, а не уничтожает, поэтому при возврате список
    и выбранный партнер остаются на месте.
    """

    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self.partners = []
        self.selected = None
        self.logo_image = None
        self.title(WINDOW_TITLE)
        self.geometry("900x700")
        self.minsize(760, 520)
        self.configure(background=ui_style.BACKGROUND)
        ui_style.apply_theme(self)
        app_resources.set_window_icon(self)
        self.build_header()
        self.build_toolbar()
        self.build_status_bar()
        self.cards = CardList(self, self.select_partner, self.edit_partner)
        self.cards.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.load_partners()

    def build_header(self):
        """Шапка: логотип, заголовок и добавление партнера."""
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
        self.header_buttons = tk.Frame(header, background=ui_style.BACKGROUND)
        self.header_buttons.pack(side="right", padx=(0, 24))
        ttk.Button(self.header_buttons,
                   text="Добавить партнера",
                   style="Primary.TButton",
                   command=self.add_partner).pack(side="right")
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

    def build_toolbar(self):
        """Панель над списком: выбранный партнер и действия с ним."""
        toolbar = tk.Frame(self, background=ui_style.BACKGROUND)
        toolbar.pack(fill="x", side="top", padx=24, pady=14)
        self.selection_label = tk.Label(toolbar,
                                        text=NOTHING_SELECTED,
                                        anchor="w",
                                        font=ui_style.SUBTITLE_FONT,
                                        background=ui_style.BACKGROUND,
                                        foreground=ui_style.MUTED_TEXT)
        self.selection_label.pack(side="left", fill="x", expand=True)
        self.history_button = ttk.Button(toolbar,
                                         text="История продаж",
                                         style="Primary.TButton",
                                         state="disabled",
                                         command=self.show_history)
        self.history_button.pack(side="right")
        self.edit_button = ttk.Button(toolbar,
                                      text="Изменить",
                                      style="Card.TButton",
                                      state="disabled",
                                      command=self.edit_selected)
        self.edit_button.pack(side="right", padx=(0, 10))
        ttk.Button(toolbar,
                   text="Обновить",
                   style="Card.TButton",
                   command=self.load_partners).pack(side="right",
                                                    padx=(0, 10))

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
            self.restore_selection()
            self.show_status(f"Нет связи с базой данных: {first_line(error)}")
            dialogs.show_error(self, DATABASE_MESSAGE.format(
                first_line(error)))
            return
        self.cards.show_partners(self.partners)
        self.restore_selection()
        self.show_status(f"Партнеров загружено: {len(self.partners)}. "
                         "Двойной щелчок по карточке открывает ее.")

    def restore_selection(self):
        """Сохранить выбор после перечитывания списка, если партнер есть.

        Список пересоздается целиком, поэтому выбор ищется заново по id:
        старый словарь партнера мог устареть.
        """
        selected_id = self.selected["id"] if self.selected else None
        self.selected = None
        for partner in self.partners:
            if partner["id"] == selected_id:
                self.selected = partner
        self.cards.mark_selected(selected_id if self.selected else None)
        self.update_toolbar()

    def select_partner(self, partner: dict):
        """Запомнить выбранного партнера и включить кнопки действий."""
        self.selected = partner
        self.cards.mark_selected(partner["id"])
        self.update_toolbar()

    def update_toolbar(self):
        """Показать выбранного партнера; без выбора кнопки выключены."""
        if self.selected is None:
            text = NOTHING_SELECTED
            state = "disabled"
        else:
            text = (f'Выбран: {self.selected["partner_type"]} '
                    f'«{self.selected["name"]}»')
            state = "normal"
        self.selection_label.configure(text=text)
        self.edit_button.configure(state=state)
        self.history_button.configure(state=state)

    def add_partner(self):
        """Перейти к карточке нового партнера."""
        self.navigator.open_editor()

    def edit_partner(self, partner: dict):
        """Перейти к карточке указанного партнера."""
        self.navigator.open_editor(partner)

    def edit_selected(self):
        """Открыть карточку выбранного партнера."""
        if self.selected is not None:
            self.edit_partner(self.selected)

    def show_history(self):
        """Открыть историю продаж выбранного партнера.

        В новое окно передается только id: историю и название партнера
        окно само читает из базы, чтобы показать актуальные данные.
        """
        if self.selected is not None:
            self.navigator.open_history(self.selected["id"])

    def on_return(self, reload: bool = False):
        """Показать реестр после другого окна.

        После сохранения список перечитывается из базы, после отмены —
        остается тем же, что и был: лишний запрос не нужен.
        """
        if reload:
            self.load_partners()
            return
        self.show_status(f"Вы вернулись в реестр. "
                         f"Партнеров в списке: {len(self.partners)}.")
