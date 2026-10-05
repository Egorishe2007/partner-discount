"""Диалоговые окна приложения: ошибка, предупреждение, уведомление.

Все три типа собраны в одном месте, чтобы у каждого окна был свой
заголовок и своя пиктограмма, а окна приложения вызывали их одной
строкой.
"""

from tkinter import messagebox

ERROR_TITLE = "CRM: Ошибка"
WARNING_TITLE = "CRM: Предупреждение"
INFO_TITLE = "CRM: Уведомление"


def show_error(parent, message: str):
    """Ошибка: красный крестик, операция не выполнена."""
    messagebox.showerror(ERROR_TITLE, message, parent=parent)


def show_warning(parent, message: str) -> bool:
    """Предупреждение с восклицательным знаком.

    Возвращает True, если менеджер подтвердил действие, и False,
    если передумал: вопрос задается перед необратимой потерей данных.
    """
    return messagebox.askokcancel(WARNING_TITLE, message,
                                  icon=messagebox.WARNING, parent=parent)


def show_info(parent, message: str):
    """Уведомление: инфо-значок, операция прошла успешно."""
    messagebox.showinfo(INFO_TITLE, message, parent=parent)
