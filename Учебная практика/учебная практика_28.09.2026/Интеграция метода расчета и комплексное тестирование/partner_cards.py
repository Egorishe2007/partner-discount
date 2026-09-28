"""Карточки партнеров для главной формы."""

import tkinter as tk
from tkinter import ttk

import ui_style

CARD_PADDING = 14


class PartnerCard(tk.Frame):
    """Карточка партнера по макету из руководства по стилю.

    Щелчок выбирает партнера, двойной щелчок открывает его карточку на
    редактирование. Обработчики вешаются и на подписи: иначе щелчок по
    тексту до карточки не доходит.
    """

    def __init__(self, master, partner: dict, on_select, on_open):
        super().__init__(master,
                         background=ui_style.CARD_BACKGROUND,
                         highlightbackground=ui_style.BORDER,
                         highlightcolor=ui_style.BORDER,
                         highlightthickness=ui_style.CARD_BORDER_WIDTH,
                         cursor="hand2")
        self.partner = partner
        self.on_select = on_select
        self.on_open = on_open
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
        self.bind_clicks(self)

    def add_label(self, text, font, color, row, column, pady):
        """Разместить одну подпись внутри карточки."""
        sticky = "ne" if column else "w"
        label = tk.Label(self, text=text, font=font,
                         background=ui_style.CARD_BACKGROUND,
                         foreground=color, cursor="hand2")
        label.grid(row=row, column=column, sticky=sticky, padx=18, pady=pady)
        self.bind_clicks(label)

    def bind_clicks(self, widget):
        """Связать щелчки по виджету с выбором и открытием партнера."""
        widget.bind("<Button-1>", self.select_partner)
        widget.bind("<Double-Button-1>", self.open_partner)

    def select_partner(self, event=None):
        """Выбрать партнера этой карточки."""
        self.on_select(self.partner)

    def open_partner(self, event=None):
        """Открыть партнера этой карточки на редактирование."""
        self.on_open(self.partner)

    def set_selected(self, selected: bool):
        """Выделить карточку темной рамкой или снять выделение."""
        color = ui_style.TEXT if selected else ui_style.BORDER
        width = (ui_style.SELECTED_BORDER_WIDTH if selected
                 else ui_style.CARD_BORDER_WIDTH)
        self.configure(highlightbackground=color,
                       highlightcolor=color,
                       highlightthickness=width)


class CardList(tk.Frame):
    """Прокручиваемый список карточек партнеров."""

    def __init__(self, master, on_select, on_open):
        super().__init__(master,
                         background=ui_style.BACKGROUND,
                         highlightbackground=ui_style.BORDER,
                         highlightcolor=ui_style.BORDER,
                         highlightthickness=1)
        self.on_select = on_select
        self.on_open = on_open
        self.cards = {}
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
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.body.bind("<MouseWheel>", self.on_mouse_wheel)

    def on_body_resize(self, event):
        """Обновить область прокрутки под размер содержимого."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        """Растянуть карточки на всю ширину списка."""
        self.canvas.itemconfigure(self.body_id, width=event.width)

    def on_mouse_wheel(self, event):
        """Прокрутить список колесом мыши."""
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def bind_wheel(self, widget):
        """Включить прокрутку колесом, когда курсор стоит на карточке.

        Колесо получает тот виджет, что под курсором, поэтому
        обработчик вешается на карточку и на все подписи внутри нее.
        """
        widget.bind("<MouseWheel>", self.on_mouse_wheel)
        for child in widget.winfo_children():
            self.bind_wheel(child)

    def clear(self):
        """Убрать все карточки из списка."""
        for card in self.body.winfo_children():
            card.destroy()
        self.cards = {}

    def show_partners(self, partners: list):
        """Показать карточки партнеров."""
        self.clear()
        for partner in partners:
            card = PartnerCard(self.body, partner,
                               self.on_select, self.on_open)
            card.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
            self.bind_wheel(card)
            self.cards[partner["id"]] = card
        tk.Frame(self.body,
                 background=ui_style.BACKGROUND,
                 height=CARD_PADDING).pack(fill="x")

    def mark_selected(self, partner_id):
        """Выделить карточку выбранного партнера, с остальных снять."""
        for card_id, card in self.cards.items():
            card.set_selected(card_id == partner_id)
