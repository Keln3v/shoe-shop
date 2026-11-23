from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.catalog_logic import (
    ALL_CATEGORIES,
    SORT_NONE,
    SORT_PRICE_ASC,
    SORT_PRICE_DESC,
    filter_and_sort_products,
    prepare_catalog,
)
from app.database import get_catalog, get_categories
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.messages import show_app_error
from app.ui.product_card import ProductCard


class CatalogPage(BasePage):
    page_title = "Каталог товаров"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.products = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Панель поиска, сортировки и фильтрации (только для авторизованных пользователей)
        self.controls_panel = QFrame()
        self.controls_panel.setObjectName("panel")
        controls = QHBoxLayout(self.controls_panel)
        self.search_edit = QLineEdit()
        self.search_edit.setMaxLength(100)
        self.search_edit.setPlaceholderText("Поиск по наименованию и описанию")
        self.search_edit.textChanged.connect(self.refresh_list)
        controls.addWidget(self.search_edit, 3)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([SORT_NONE, SORT_PRICE_ASC, SORT_PRICE_DESC])
        self.sort_combo.currentIndexChanged.connect(self.refresh_list)
        controls.addWidget(self.sort_combo, 1)
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.refresh_list)
        controls.addWidget(self.category_combo, 1)
        layout.addWidget(self.controls_panel)

        # Строка с количеством найденных моделей и кнопками перехода
        bar = QHBoxLayout()
        self.count_label = QLabel()
        self.count_label.setObjectName("hint")
        bar.addWidget(self.count_label)
        bar.addStretch(1)
        self.orders_button = QPushButton("Список заказов")
        self.orders_button.clicked.connect(lambda: self.main_window.navigate("orders"))
        bar.addWidget(self.orders_button)
        self.cart_button = QPushButton("Оформление заказа")
        self.cart_button.setProperty("primary", True)
        self.cart_button.clicked.connect(lambda: self.main_window.navigate("cart"))
        bar.addWidget(self.cart_button)
        layout.addLayout(bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 6, 0)
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll, 1)

    def on_show(self, **kwargs):
        authorized = self.state.is_authorized
        self.controls_panel.setVisible(authorized)
        self.cart_button.setVisible(authorized)
        self.orders_button.setVisible(self.state.can_manage_orders)
        self._update_cart_button()
        try:
            self.products = prepare_catalog(get_catalog())
            self._reload_categories(get_categories())
        except AppError as error:
            self.products = []
            show_app_error(self, error)
        self.refresh_list()

    def _update_cart_button(self):
        count = sum(item["quantity"] for item in self.state.cart)
        self.cart_button.setText(f"Оформление заказа ({count})" if count else "Оформление заказа")

    def _reload_categories(self, categories):
        selected = self.category_combo.currentText() or ALL_CATEGORIES
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem(ALL_CATEGORIES)
        self.category_combo.addItems(categories)
        index = self.category_combo.findText(selected)
        self.category_combo.setCurrentIndex(max(index, 0))
        self.category_combo.blockSignals(False)

    def refresh_list(self, *_):
        if self.state.is_authorized:
            visible = filter_and_sort_products(
                self.products,
                self.search_edit.text(),
                self.category_combo.currentText() or ALL_CATEGORIES,
                self.sort_combo.currentText(),
            )
        else:
            visible = self.products
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for product in visible:
            card = ProductCard(product, clickable=self.state.is_authorized)
            card.clicked.connect(self.open_product)
            self.list_layout.addWidget(card)
        if not visible:
            empty = QLabel("По вашему запросу ничего не найдено. Измените условия поиска или фильтр.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setObjectName("hint")
            self.list_layout.addWidget(empty)
        self.list_layout.addStretch(1)
        text = f"Найдено моделей: {len(visible)}"
        if not self.state.is_authorized:
            text += ". Чтобы искать товары и оформлять заказы, войдите в систему."
        self.count_label.setText(text)

    def open_product(self, product):
        self.main_window.navigate("product", product=product)
