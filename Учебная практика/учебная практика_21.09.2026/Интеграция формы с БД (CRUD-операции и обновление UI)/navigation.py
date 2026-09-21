"""Переключение экранов приложения: реестр и карточка партнера."""

from main_window import MainWindow
from partner_edit_window import PartnerEditWindow


class Navigator:
    """Последовательный переход между окнами приложения.

    На экране всегда одно окно: при переходе к карточке партнера
    реестр скрывается (withdraw), при возврате — показывается снова
    (deiconify). Главное окно при этом не пересоздается, поэтому
    загруженный список партнеров и позиция прокрутки не теряются.
    """

    def __init__(self):
        self.main_window = MainWindow(self)
        self.editor = None

    def start(self):
        """Показать реестр партнеров и запустить цикл событий."""
        self.main_window.mainloop()

    def open_editor(self, partner: dict = None):
        """Открыть карточку партнера, скрыв реестр.

        Ссылка на открытое окно хранится в self.editor: пока оно
        живо, повторное нажатие кнопки не создает второе такое же
        окно, а поднимает уже открытое.
        """
        if self.editor_is_open():
            self.editor.lift()
            self.editor.focus_force()
            return self.editor
        self.main_window.withdraw()
        self.editor = PartnerEditWindow(self.main_window, self, partner)
        return self.editor

    def back_to_main(self, reload: bool = False):
        """Закрыть карточку партнера и вернуться в реестр.

        reload=True приходит после сохранения: реестр перечитывает
        базу, чтобы новая или измененная запись сразу была в списке.
        """
        if self.editor_is_open():
            self.editor.destroy()
        self.editor = None
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()
        self.main_window.on_return(reload)

    def editor_is_open(self) -> bool:
        """Проверить, что карточка партнера сейчас открыта."""
        return self.editor is not None and self.editor.winfo_exists()
