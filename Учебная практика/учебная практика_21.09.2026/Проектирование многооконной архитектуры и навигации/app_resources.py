"""Логотип и иконка приложения из папки resources."""

import os
import tkinter as tk

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "resources")
LOGO_FILE = "logo.png"
ICON_FILE = "icon.ico"


def set_window_icon(window):
    """Поставить окну иконку приложения, если файл на месте."""
    icon_path = os.path.join(RESOURCES_DIR, ICON_FILE)
    if not os.path.exists(icon_path):
        return
    try:
        window.iconbitmap(icon_path)
    except tk.TclError:
        return


def load_logo():
    """Вернуть картинку логотипа или None, если файла нет.

    Ссылку на картинку обязано хранить окно: Tkinter сам ее не держит,
    и без ссылки логотип исчезает после сборки мусора.
    """
    logo_path = os.path.join(RESOURCES_DIR, LOGO_FILE)
    if not os.path.exists(logo_path):
        return None
    try:
        return tk.PhotoImage(file=logo_path)
    except tk.TclError:
        return None
