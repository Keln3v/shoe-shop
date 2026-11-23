import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from app.config import LOGO_FILE
from app.constants import APP_NAME
from app.database import get_user_by_login
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.messages import show_app_error, show_warning

LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9_.]+$")
EMPTY_LOGIN_MESSAGE = "Логин не введён. Введите логин из списка пользователей системы."
INVALID_LOGIN_MESSAGE = "Логин может содержать только латинские буквы, цифры, точку и подчёркивание. Проверьте раскладку клавиатуры."


class LoginPage(BasePage):
    page_title = "Авторизация"

    def __init__(self, main_window):
        super().__init__(main_window)
        outer = QHBoxLayout(self)
        outer.addStretch(1)

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(420)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(QPixmap(str(LOGO_FILE)).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Логин:"))
        self.login_edit = QLineEdit()
        self.login_edit.setMaxLength(50)
        self.login_edit.setPlaceholderText("Введите логин")
        self.login_edit.returnPressed.connect(self.login)
        self.login_edit.textChanged.connect(self._validate_while_typing)
        layout.addWidget(self.login_edit)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("error")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        login_button = QPushButton("Войти")
        login_button.setProperty("primary", True)
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        guest_button = QPushButton("Войти как гость")
        guest_button.clicked.connect(self.login_as_guest)
        layout.addWidget(guest_button)

        column = QVBoxLayout()
        column.addStretch(1)
        column.addWidget(panel)
        column.addStretch(2)
        outer.addLayout(column)
        outer.addStretch(1)

    def on_show(self, **kwargs):
        self.login_edit.clear()
        self.login_edit.setFocus()

    def _validate_while_typing(self, text):
        if text and not LOGIN_PATTERN.match(text):
            self.hint_label.setText(INVALID_LOGIN_MESSAGE)
        else:
            self.hint_label.setText("")

    def login(self):
        login = self.login_edit.text().strip()
        if not login:
            show_warning(self, EMPTY_LOGIN_MESSAGE, "Логин не введён")
            return
        if not LOGIN_PATTERN.match(login):
            show_warning(self, INVALID_LOGIN_MESSAGE, "Некорректный логин")
            return
        try:
            user = get_user_by_login(login)
        except AppError as error:
            show_app_error(self, error)
            return
        if user is None:
            show_warning(
                self,
                f"Пользователь с логином «{login}» не найден. Проверьте логин или войдите как гость.",
                "Пользователь не найден",
            )
            return
        self.state.user = user
        self.main_window.reset_to("catalog")

    def login_as_guest(self):
        self.state.user = None
        self.main_window.reset_to("catalog")
