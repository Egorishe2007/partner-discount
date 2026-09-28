"""Оформление интерфейса: цвета и шрифты из руководства по стилю."""

from tkinter import ttk

BACKGROUND = "#FFFFFF"
CARD_BACKGROUND = "#FFFFFF"
BORDER = "#B3B3B3"
SOFT_BORDER = "#E0E0E0"
TEXT = "#1A1A1A"
MUTED_TEXT = "#404040"
HINT_TEXT = "#8C8C8C"
BUTTON_ACTIVE = "#F0F0F0"
PRIMARY_ACTIVE = "#333333"
SCROLL_THUMB = "#D0D0D0"
STRIPE_BACKGROUND = "#F7F7F7"

FONT_FAMILY = "Segoe UI"
TITLE_FONT = (FONT_FAMILY, 16, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 10)
CARD_TITLE_FONT = (FONT_FAMILY, 13)
CARD_TEXT_FONT = (FONT_FAMILY, 9)
FIELD_LABEL_FONT = (FONT_FAMILY, 9)
FIELD_FONT = (FONT_FAMILY, 10)
BUTTON_FONT = (FONT_FAMILY, 10)
STATUS_FONT = (FONT_FAMILY, 9)
TABLE_FONT = (FONT_FAMILY, 10)
TABLE_HEADING_FONT = (FONT_FAMILY, 10, "bold")

CARD_BORDER_WIDTH = 1
SELECTED_BORDER_WIDTH = 2


def apply_theme(root):
    """Настроить внешний вид кнопок, полей, таблиц и полосы прокрутки.

    Стили ttk общие для всего приложения, поэтому функция вызывается
    один раз для главного окна, а остальные окна берут уже
    настроенные стили по имени.
    """
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Card.TButton",
                    background=CARD_BACKGROUND,
                    foreground=TEXT,
                    font=BUTTON_FONT,
                    borderwidth=1,
                    bordercolor=BORDER,
                    lightcolor=CARD_BACKGROUND,
                    darkcolor=CARD_BACKGROUND,
                    focuscolor=CARD_BACKGROUND,
                    padding=(18, 9))
    style.map("Card.TButton",
              background=[("disabled", CARD_BACKGROUND),
                          ("active", BUTTON_ACTIVE),
                          ("pressed", BUTTON_ACTIVE)],
              foreground=[("disabled", HINT_TEXT)],
              bordercolor=[("disabled", SOFT_BORDER),
                           ("active", TEXT)])
    style.configure("Primary.TButton",
                    background=TEXT,
                    foreground=BACKGROUND,
                    font=BUTTON_FONT,
                    borderwidth=1,
                    bordercolor=TEXT,
                    lightcolor=TEXT,
                    darkcolor=TEXT,
                    focuscolor=TEXT,
                    padding=(18, 9))
    style.map("Primary.TButton",
              background=[("disabled", SOFT_BORDER),
                          ("active", PRIMARY_ACTIVE),
                          ("pressed", PRIMARY_ACTIVE)],
              foreground=[("disabled", HINT_TEXT)],
              bordercolor=[("disabled", SOFT_BORDER),
                           ("active", PRIMARY_ACTIVE)],
              lightcolor=[("disabled", SOFT_BORDER)],
              darkcolor=[("disabled", SOFT_BORDER)])
    style.configure("Card.TEntry",
                    fieldbackground=CARD_BACKGROUND,
                    foreground=TEXT,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER,
                    insertcolor=TEXT,
                    borderwidth=1,
                    padding=(8, 7))
    style.map("Card.TEntry", bordercolor=[("focus", TEXT)])
    style.configure("Card.TCombobox",
                    fieldbackground=CARD_BACKGROUND,
                    background=CARD_BACKGROUND,
                    foreground=TEXT,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER,
                    arrowcolor=TEXT,
                    borderwidth=1,
                    padding=(8, 7))
    style.map("Card.TCombobox",
              bordercolor=[("focus", TEXT)],
              fieldbackground=[("readonly", CARD_BACKGROUND)],
              selectbackground=[("readonly", CARD_BACKGROUND)],
              selectforeground=[("readonly", TEXT)])
    style.configure("Card.TSpinbox",
                    fieldbackground=CARD_BACKGROUND,
                    background=CARD_BACKGROUND,
                    foreground=TEXT,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER,
                    arrowcolor=TEXT,
                    insertcolor=TEXT,
                    borderwidth=1,
                    padding=(8, 7))
    style.map("Card.TSpinbox", bordercolor=[("focus", TEXT)])
    style.configure("History.Treeview",
                    background=CARD_BACKGROUND,
                    fieldbackground=CARD_BACKGROUND,
                    foreground=TEXT,
                    font=TABLE_FONT,
                    rowheight=32,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER,
                    borderwidth=1)
    style.map("History.Treeview",
              background=[("selected", SOFT_BORDER)],
              foreground=[("selected", TEXT)])
    style.configure("History.Treeview.Heading",
                    background=BUTTON_ACTIVE,
                    foreground=TEXT,
                    font=TABLE_HEADING_FONT,
                    bordercolor=SOFT_BORDER,
                    lightcolor=BUTTON_ACTIVE,
                    darkcolor=BUTTON_ACTIVE,
                    relief="flat",
                    padding=(10, 8))
    style.map("History.Treeview.Heading",
              background=[("active", SOFT_BORDER)])
    style.configure("Vertical.TScrollbar",
                    background=SCROLL_THUMB,
                    troughcolor=BACKGROUND,
                    bordercolor=SOFT_BORDER,
                    lightcolor=SCROLL_THUMB,
                    darkcolor=SCROLL_THUMB,
                    arrowcolor=TEXT,
                    borderwidth=0)
