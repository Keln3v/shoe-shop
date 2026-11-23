"""Точка входа: приложение «Чудо Обувь» — система ОФОРМЛЕНИЯЯЯ заказов обуви."""

import sys

from PyQt5.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.styles import apply_style


def set_windows_app_id():
    """Чтобы иконка приложения отображалась и на панели задач Windows."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "chudo.obuv.shoeshop"
        )
    except (AttributeError, OSError):
        pass


def main():
    set_windows_app_id()
    app = QApplication(sys.argv)
    apply_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
