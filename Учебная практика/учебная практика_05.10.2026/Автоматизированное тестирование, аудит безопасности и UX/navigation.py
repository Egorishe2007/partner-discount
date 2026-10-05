"""Переключение экранов приложения: реестр и дочерние окна."""

from main_window import MainWindow
from material_calculator_window import MaterialCalculatorWindow
from partner_edit_window import PartnerEditWindow
from partner_history_window import PartnerHistoryWindow


class Navigator:
    """Последовательный переход между окнами приложения.

    На экране всегда одно окно: при переходе к карточке партнера, к
    истории продаж или к расчету материалов реестр скрывается
    (withdraw), при возврате — показывается снова (deiconify). Главное
    окно при этом не пересоздается, поэтому загруженный список и
    выбранный партнер не теряются.
    """

    def __init__(self):
        self.main_window = MainWindow(self)
        self.child = None

    def start(self):
        """Показать реестр партнеров и запустить цикл событий."""
        self.main_window.mainloop()

    def open_editor(self, partner: dict = None):
        """Открыть карточку партнера: добавление или редактирование."""
        return self.open_child(PartnerEditWindow, partner)

    def open_history(self, partner_id: int):
        """Открыть историю реализации продукции партнера по его id."""
        return self.open_child(PartnerHistoryWindow, partner_id)

    def open_calculator(self):
        """Открыть окно расчета материалов."""
        return self.open_child(MaterialCalculatorWindow)

    def open_child(self, window_class, *arguments):
        """Открыть дочернее окно, спрятав реестр.

        Ссылка на открытое окно хранится в self.child: пока оно живо,
        повторный вызов не создает второе окно, а поднимает открытое.
        """
        if self.child_is_open():
            self.child.lift()
            self.child.focus_force()
            return self.child
        self.main_window.withdraw()
        self.child = window_class(self.main_window, self, *arguments)
        return self.child

    def back_to_main(self, reload: bool = False):
        """Закрыть дочернее окно и вернуться в реестр.

        reload=True приходит после сохранения: реестр перечитывает
        базу, чтобы новая или измененная запись сразу была в списке.
        """
        if self.child_is_open():
            self.child.destroy()
        self.child = None
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()
        self.main_window.on_return(reload)

    def child_is_open(self) -> bool:
        """Проверить, что дочернее окно сейчас открыто."""
        return self.child is not None and self.child.winfo_exists()
