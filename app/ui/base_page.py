from PyQt5.QtWidgets import QWidget


class BasePage(QWidget):
    """Страница приложения. Заголовок окна формируется из page_title."""

    page_title = ""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.state = main_window.state

    def on_show(self, **kwargs):
        """Вызывается при каждом открытии страницы: здесь загружаются актуальные данные."""
