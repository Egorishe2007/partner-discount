"""Окно истории реализации продукции выбранного партнера."""

import tkinter as tk
from contextlib import closing
from tkinter import ttk

from psycopg2 import Error as DatabaseError

import app_resources
import dialogs
import ui_style
from app_log import get_logger
from messages import database_message
from db import get_connection
from partner_cards import partner_title
from partner_service import get_partner_with_discount, get_sales_history

TITLE_PREFIX = "CRM: История реализации продукции"
COLUMNS = (
    ("product_name", "Товар", 330, "w"),
    ("sale_date", "Дата продажи", 130, "center"),
    ("quantity", "Количество, шт.", 130, "e"),
    ("amount", "Сумма, ₽", 150, "e"),
)
RETRY_STEP = "Нажмите «Назад» и откройте историю продаж еще раз."

logger = get_logger("partner_history_window")


def first_line(error: Exception) -> str:
    """Первая строка сообщения об ошибке — для строки состояния."""
    lines = str(error).strip().splitlines()
    if not lines:
        return "неизвестная ошибка"
    return lines[0]


def format_quantity(quantity: int) -> str:
    """Количество с пробелами между разрядами: 150000 → 150 000."""
    return f"{quantity:,}".replace(",", " ")


def format_money(amount) -> str:
    """Сумма в рублях с копейками: 150000.00 → 150 000,00."""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


def format_sale_date(sale_date) -> str:
    """Дата продажи в привычном виде: 2025-03-15 → 15.03.2025."""
    return sale_date.strftime("%d.%m.%Y")


def window_title(partner: dict = None) -> str:
    """Заголовок окна с названием партнера, если он найден."""
    if partner is None:
        return TITLE_PREFIX
    return f'{TITLE_PREFIX} — {partner["name"]}'


class PartnerHistoryWindow(tk.Toplevel):
    """История отгрузок партнера: что, сколько и когда он реализовал.

    Из реестра окно получает только partner_id, а название партнера и
    его продажи читает из базы само: так в окне всегда актуальные
    данные, даже если реестр загружали давно.
    """

    def __init__(self, master, navigator, partner_id: int):
        super().__init__(master, background=ui_style.BACKGROUND)
        self.navigator = navigator
        self.partner_id = partner_id
        self.partner = None
        self.sales = []
        self.logo_image = None
        self.geometry("860x620")
        self.minsize(720, 480)
        app_resources.set_window_icon(self)
        # Крестик окна и Esc ведут туда же, куда кнопка «Назад»: иначе
        # реестр остался бы скрытым, а приложение — без окон.
        self.protocol("WM_DELETE_WINDOW", self.go_back)
        self.bind("<Escape>", self.go_back)
        error = self.load_history()
        # Окно ошибки показывается после постройки окна: иначе оно
        # открылось бы над пустым местом, а не над историей.
        self.title(window_title(self.partner))
        self.build_header()
        self.build_footer()
        self.build_table()
        self.fill_table()
        if error is not None:
            dialogs.show_error(self, database_message(
                "Не удалось загрузить историю продаж", error, RETRY_STEP))

    def load_history(self):
        """Прочитать партнера и его продажи; вернуть ошибку базы."""
        try:
            with closing(get_connection()) as connection:
                self.partner = get_partner_with_discount(connection,
                                                         self.partner_id)
                self.sales = get_sales_history(connection, self.partner_id)
        except DatabaseError as error:
            logger.error("История продаж партнера № %s не загружена: %s",
                         self.partner_id, first_line(error))
            return error
        return None

    def build_header(self):
        """Шапка: логотип компании, назначение окна и партнер."""
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
                 text="История реализации продукции",
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
        """Подзаголовок: партнер, его директор и текущая скидка."""
        if self.partner is None:
            return f"Партнер № {self.partner_id} не найден в базе данных"
        parts = [partner_title(self.partner)]
        if self.partner["director"]:
            parts.append(self.partner["director"])
        parts.append(f'скидка {self.partner["discount_percent"]}%')
        return " · ".join(parts)

    def build_table(self):
        """Таблица продаж с полосой прокрутки."""
        frame = tk.Frame(self, background=ui_style.BACKGROUND)
        frame.pack(fill="both", expand=True, padx=24, pady=20)
        self.table = ttk.Treeview(frame,
                                  style="History.Treeview",
                                  columns=[key for key, *rest in COLUMNS],
                                  show="headings",
                                  selectmode="browse")
        for key, caption, width, anchor in COLUMNS:
            self.table.heading(key, text=caption, anchor=anchor)
            self.table.column(key, width=width, anchor=anchor,
                              stretch=key == "product_name")
        self.table.tag_configure("stripe",
                                 background=ui_style.STRIPE_BACKGROUND)
        scrollbar = ttk.Scrollbar(frame,
                                  orient="vertical",
                                  command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def fill_table(self):
        """Заполнить таблицу продажами и подвести итог внизу окна."""
        for number, sale in enumerate(self.sales):
            tags = ("stripe",) if number % 2 else ()
            self.table.insert("", "end", tags=tags, values=(
                sale["product_name"],
                format_sale_date(sale["sale_date"]),
                format_quantity(sale["quantity"]),
                format_money(sale["amount"])))
        self.summary.configure(text=self.summary_text())

    def summary_text(self) -> str:
        """Итог под таблицей: число продаж и общий объем."""
        if not self.sales:
            return "Продаж у партнера пока нет."
        total = sum(sale["quantity"] for sale in self.sales)
        total_amount = sum(sale["amount"] for sale in self.sales)
        return (f"Продаж: {len(self.sales)} · реализовано "
                f"{format_quantity(total)} шт. на "
                f"{format_money(total_amount)} ₽")

    def build_footer(self):
        """Нижняя панель: итог по продажам и кнопка возврата."""
        footer = tk.Frame(self, background=ui_style.BACKGROUND)
        footer.pack(fill="x", side="bottom")
        self.summary = tk.Label(footer,
                                font=ui_style.SUBTITLE_FONT,
                                background=ui_style.BACKGROUND,
                                foreground=ui_style.MUTED_TEXT)
        self.summary.pack(side="left", padx=24, pady=16)
        ttk.Button(footer,
                   text="Назад",
                   style="Primary.TButton",
                   command=self.go_back).pack(side="right", padx=24, pady=16)
        tk.Frame(self,
                 background=ui_style.SOFT_BORDER,
                 height=1).pack(fill="x", side="bottom")

    def go_back(self, event=None):
        """Закрыть историю и вернуться на главную форму."""
        self.navigator.back_to_main()
