"""Оформление интерфейса: цвета и шрифты из руководства по стилю."""

from tkinter import ttk

BACKGROUND = "#FFFFFF"
CARD_BACKGROUND = "#FFFFFF"
BORDER = "#B3B3B3"
SOFT_BORDER = "#E0E0E0"
TEXT = "#1A1A1A"
MUTED_TEXT = "#404040"
BUTTON_ACTIVE = "#F0F0F0"
SCROLL_THUMB = "#D0D0D0"

FONT_FAMILY = "Segoe UI"
TITLE_FONT = (FONT_FAMILY, 16, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 10)
CARD_TITLE_FONT = (FONT_FAMILY, 13)
CARD_TEXT_FONT = (FONT_FAMILY, 9)
BUTTON_FONT = (FONT_FAMILY, 10)
STATUS_FONT = (FONT_FAMILY, 9)


def apply_theme(root):
    """Настроить внешний вид кнопки и полосы прокрутки."""
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
              background=[("active", BUTTON_ACTIVE),
                          ("pressed", BUTTON_ACTIVE)],
              bordercolor=[("active", TEXT)])
    style.configure("Vertical.TScrollbar",
                    background=SCROLL_THUMB,
                    troughcolor=BACKGROUND,
                    bordercolor=SOFT_BORDER,
                    lightcolor=SCROLL_THUMB,
                    darkcolor=SCROLL_THUMB,
                    arrowcolor=TEXT,
                    borderwidth=0)
