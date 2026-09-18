"""Экранная форма CRM: список партнеров и их скидок."""

import os
import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import ui_style
from db import get_connection
from partner_service import get_partners_with_discounts

WINDOW_TITLE = "CRM: Список партнеров и скидок"
WINDOW_SUBTITLE = "Объемы продаж и рассчитанные скидки партнеров"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(PROJECT_DIR, "resources")
LOGO_FILE = "logo.png"
ICON_FILE = "icon.ico"
CARD_PADDING = 14


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для строки состояния."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


class PartnerCard(tk.Frame):
    """Карточка партнера по макету из руководства по стилю."""

    def __init__(self, master, partner: dict):
        super().__init__(master,
                         background=ui_style.CARD_BACKGROUND,
                         highlightbackground=ui_style.BORDER,
                         highlightcolor=ui_style.BORDER,
                         highlightthickness=1)
        self.columnconfigure(0, weight=1)
        self.add_label(f'{partner["partner_type"]} | {partner["name"]}',
                       ui_style.CARD_TITLE_FONT, ui_style.TEXT, 0, 0, (12, 4))
        self.add_label(f'{partner["discount_percent"]}%',
                       ui_style.CARD_TITLE_FONT, ui_style.TEXT, 0, 1, (12, 4))
        details = (partner["director"],
                   partner["phone"],
                   f'Рейтинг: {partner["rating"]}')
        for number, text in enumerate(details):
            last = number == len(details) - 1
            pady = (0, 12) if last else (0, 1)
            self.add_label(text, ui_style.CARD_TEXT_FONT,
                           ui_style.MUTED_TEXT, number + 1, 0, pady)

    def add_label(self, text, font, color, row, column, pady):
        """Разместить одну подпись внутри карточки."""
        sticky = "ne" if column else "w"
        tk.Label(self, text=text, font=font,
                 background=ui_style.CARD_BACKGROUND,
                 foreground=color).grid(row=row, column=column,
                                        sticky=sticky, padx=18, pady=pady)


class CardList(tk.Frame):
    """Прокручиваемый список карточек партнеров."""

    def __init__(self, master):
        super().__init__(master,
                         background=ui_style.BACKGROUND,
                         highlightbackground=ui_style.BORDER,
                         highlightcolor=ui_style.BORDER,
                         highlightthickness=1)
        self.canvas = tk.Canvas(self,
                                background=ui_style.BACKGROUND,
                                highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self,
                                       orient="vertical",
                                       command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, background=ui_style.BACKGROUND)
        self.body_id = self.canvas.create_window((0, 0),
                                                 window=self.body,
                                                 anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.body.bind("<Configure>", self.on_body_resize)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def on_body_resize(self, event):
        """Обновить область прокрутки под размер содержимого."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        """Растянуть карточки на всю ширину списка."""
        self.canvas.itemconfigure(self.body_id, width=event.width)

    def on_mouse_wheel(self, event):
        """Прокрутить список колесом мыши."""
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def clear(self):
        """Убрать все карточки из списка."""
        for card in self.body.winfo_children():
            card.destroy()

    def show_partners(self, partners: list):
        """Показать карточки партнеров."""
        self.clear()
        for partner in partners:
            card = PartnerCard(self.body, partner)
            card.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        tk.Frame(self.body,
                 background=ui_style.BACKGROUND,
                 height=CARD_PADDING).pack(fill="x")


class PartnerApp(tk.Tk):
    """Главное окно: шапка с логотипом и список партнеров."""

    def __init__(self):
        super().__init__()
        self.logo_image = None
        self.title(WINDOW_TITLE)
        self.geometry("900x660")
        self.minsize(760, 480)
        self.configure(background=ui_style.BACKGROUND)
        ui_style.apply_theme(self)
        self.set_window_icon()
        self.build_header()
        self.build_status_bar()
        self.cards = CardList(self)
        self.cards.pack(fill="both", expand=True, padx=24, pady=20)
        self.load_partners()

    def set_window_icon(self):
        """Поставить иконку приложения из папки ресурсов."""
        icon_path = os.path.join(RESOURCES_DIR, ICON_FILE)
        if not os.path.exists(icon_path):
            return
        try:
            self.iconbitmap(icon_path)
        except tk.TclError:
            return

    def build_header(self):
        """Шапка: логотип компании, заголовок и кнопка обновления."""
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
        ttk.Button(header,
                   text="Обновить",
                   style="Card.TButton",
                   command=self.load_partners).pack(side="right", padx=24)
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="top")

    def place_logo(self, header):
        """Показать логотип компании из папки ресурсов."""
        logo_path = os.path.join(RESOURCES_DIR, LOGO_FILE)
        if not os.path.exists(logo_path):
            return
        try:
            self.logo_image = tk.PhotoImage(file=logo_path)
        except tk.TclError:
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
                partners = get_partners_with_discounts(connection)
        except DatabaseError as error:
            self.cards.clear()
            self.show_status(f"Нет связи с базой данных: {first_line(error)}")
            return
        self.cards.show_partners(partners)
        self.show_status(f"Партнеров загружено: {len(partners)}")


def main():
    PartnerApp().mainloop()


if __name__ == "__main__":
    main()
