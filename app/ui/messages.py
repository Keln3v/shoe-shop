"""Окна сообщений с заголовком и пиктограммой, соответствующими типу сообщения."""
from PyQt5.QtWidgets import QMessageBox

from app.errors import DatabaseConnectionError


def _show_box(parent, icon, title, text):
    box = QMessageBox(icon, title, text, QMessageBox.NoButton, parent)
    box.addButton("ОК", QMessageBox.AcceptRole)
    box.exec_()


def show_error(parent, text, title="Ошибка"):
    _show_box(parent, QMessageBox.Critical, title, text)


def show_warning(parent, text, title="Предупреждение"):
    _show_box(parent, QMessageBox.Warning, title, text)


def show_info(parent, text, title="Информация"):
    _show_box(parent, QMessageBox.Information, title, text)


def ask_confirmation(parent, text, title="Подтверждение"):
    box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, parent)
    yes_button = box.addButton("Да", QMessageBox.YesRole)
    box.addButton("Нет", QMessageBox.NoRole)
    box.exec_()
    return box.clickedButton() is yes_button


def show_app_error(parent, error):
    """Показывает ошибку приложения (база данных, настройки, правила заказа)."""
    if isinstance(error, DatabaseConnectionError):
        show_error(parent, str(error), "Ошибка подключения")
    else:
        show_error(parent, str(error))
