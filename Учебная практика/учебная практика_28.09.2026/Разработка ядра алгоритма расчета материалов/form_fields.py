"""Поля карточки партнера: подсказки в полях и всплывающие пояснения."""

import tkinter as tk
from tkinter import ttk

import ui_style


class Tooltip:
    """Всплывающая подсказка, которая появляется по наведению мыши.

    Нужна там, где формат ввода важен, а плейсхолдер уже не виден:
    как только менеджер начал печатать, серая подсказка в поле пропадает.
    """

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.window = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, event=None):
        """Показать подсказку под полем."""
        if self.window is not None:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        # overrideredirect убирает у подсказки рамку и заголовок:
        # иначе это было бы обычное окно поверх карточки.
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.geometry(f"+{x}+{y}")
        tk.Label(self.window,
                 text=self.text,
                 font=ui_style.STATUS_FONT,
                 background=ui_style.TEXT,
                 foreground=ui_style.BACKGROUND,
                 padx=8,
                 pady=4).pack()

    def hide(self, event=None):
        """Убрать подсказку с экрана."""
        if self.window is None:
            return
        self.window.destroy()
        self.window = None


class HintEntry(ttk.Entry):
    """Текстовое поле с подсказкой формата внутри.

    Плейсхолдеров в Tkinter нет, поэтому подсказка — это обычный серый
    текст: он лежит в пустом поле и убирается, как только поле получает
    фокус. Значение поля читается через get_value, чтобы подсказка
    случайно не уехала в базу как данные партнера.
    """

    def __init__(self, master, hint: str = "", **options):
        super().__init__(master,
                         style="Card.TEntry",
                         font=ui_style.FIELD_FONT,
                         **options)
        self.hint = hint
        self.hint_shown = False
        if hint:
            self.bind("<FocusIn>", self.hide_hint)
            self.bind("<FocusOut>", self.show_hint)
            self.show_hint()

    def show_hint(self, event=None):
        """Вернуть подсказку в поле, если менеджер ничего не ввел."""
        if not self.hint or self.get():
            return
        self.hint_shown = True
        self.configure(foreground=ui_style.HINT_TEXT)
        self.insert(0, self.hint)

    def hide_hint(self, event=None):
        """Убрать подсказку перед вводом."""
        if not self.hint_shown:
            return
        self.hint_shown = False
        self.delete(0, "end")
        self.configure(foreground=ui_style.TEXT)

    def get_value(self) -> str:
        """Вернуть введенное значение; подсказка данными не считается."""
        if self.hint_shown:
            return ""
        return self.get().strip()

    def set_value(self, value):
        """Подставить в поле значение партнера из базы."""
        self.hint_shown = False
        self.delete(0, "end")
        if value in (None, ""):
            self.show_hint()
            return
        self.configure(foreground=ui_style.TEXT)
        self.insert(0, str(value))


class TypeBox(ttk.Combobox):
    """Выпадающий список с типом партнера."""

    def __init__(self, master, values, **options):
        # state="readonly": тип берется строго из списка, вписать свой
        # вариант с клавиатуры нельзя — в базе тип ограничен по длине
        # и должен совпадать у всех записей.
        super().__init__(master,
                         style="Card.TCombobox",
                         font=ui_style.FIELD_FONT,
                         values=values,
                         state="readonly",
                         **options)
        self.set(values[0])

    def get_value(self) -> str:
        """Вернуть выбранный тип партнера."""
        return self.get().strip()

    def set_value(self, value):
        """Выбрать тип партнера из базы; неизвестный тоже покажем."""
        self.set("" if value is None else str(value))


class RatingBox(ttk.Spinbox):
    """Поле рейтинга: целое неотрицательное число."""

    def __init__(self, master, maximum=100, **options):
        super().__init__(master,
                         style="Card.TSpinbox",
                         font=ui_style.FIELD_FONT,
                         from_=0,
                         to=maximum,
                         increment=1,
                         **options)
        self.set(0)

    def get_value(self) -> str:
        """Вернуть рейтинг как текст: проверка числа — при сохранении."""
        return self.get().strip()

    def set_value(self, value):
        """Подставить рейтинг партнера из базы."""
        self.delete(0, "end")
        self.insert(0, 0 if value is None else value)
