"""Главное окно: шапка с логотипом, ФИО пользователя и кнопкой «Назад», страницы приложения."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from app.config import ICON_FILE, LOGO_FILE
from app.constants import APP_NAME
from app.ui.app_state import AppState
from app.ui.cart_page import CartPage
from app.ui.catalog_page import CatalogPage
from app.ui.login_page import LoginPage
from app.ui.order_details_page import OrderDetailsPage
from app.ui.orders_page import OrdersPage
from app.ui.product_page import ProductPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.history = []
        self.current_key = None
        self.current_kwargs = {}

        self.setWindowIcon(QIcon(str(ICON_FILE)))
        self.setMinimumSize(1000, 700)
        self.resize(1180, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.pages = {
            "login": LoginPage(self),
            "catalog": CatalogPage(self),
            "product": ProductPage(self),
            "cart": CartPage(self),
            "orders": OrdersPage(self),
            "order_details": OrderDetailsPage(self),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.reset_to("login")

    def _build_header(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        self.logo_label = QLabel()
        self.logo_label.setPixmap(
            QPixmap(str(LOGO_FILE)).scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        layout.addWidget(self.logo_label)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.user_label)

        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        self.logout_button = QPushButton("Выйти")
        self.logout_button.clicked.connect(self.logout)
        layout.addWidget(self.logout_button)
        return header

    # ----- навигация -----
    def navigate(self, key, **kwargs):
        """Переход на страницу с сохранением текущей в истории (для кнопки «Назад»)."""
        if self.current_key is not None:
            self.history.append((self.current_key, self.current_kwargs))
        self._show(key, kwargs)

    def go_back(self):
        if self.history:
            key, kwargs = self.history.pop()
            self._show(key, kwargs)

    def reset_to(self, key, **kwargs):
        self.history.clear()
        self._show(key, kwargs)

    def logout(self):
        self.state.logout()
        self.reset_to("login")

    def _show(self, key, kwargs):
        page = self.pages[key]
        self.current_key = key
        self.current_kwargs = kwargs
        self.stack.setCurrentWidget(page)
        page.on_show(**kwargs)
        self._update_header(page)

    def _update_header(self, page):
        is_login = self.current_key == "login"
        self.setWindowTitle(f"{APP_NAME} — {page.page_title}")
        self.title_label.setText(page.page_title)
        self.logo_label.setVisible(not is_login)
        self.user_label.setVisible(not is_login)
        self.user_label.setText(self.state.user_full_name)
        self.back_button.setVisible(bool(self.history))
        self.logout_button.setVisible(not is_login)
