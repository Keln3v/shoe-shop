from decimal import Decimal

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.catalog_logic import format_price
from app.database import create_order, get_all_users
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.messages import ask_confirmation, show_app_error, show_info, show_warning

COLUMNS = ["Товар", "Размер", "Количество", "Цена за единицу", "Сумма"]


class CartPage(BasePage):
    page_title = "Оформление заказа"

    def __init__(self, main_window):
        super().__init__(main_window)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        client_row = QHBoxLayout()
        self.client_caption = QLabel("<b>Клиент:</b>")
        client_row.addWidget(self.client_caption)
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(320)
        client_row.addWidget(self.client_combo)
        self.client_label = QLabel()
        client_row.addWidget(self.client_label)
        client_row.addStretch(1)
        layout.addLayout(client_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in (1, 2, 3, 4):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)

        buttons = QHBoxLayout()
        remove_button = QPushButton("Удалить позицию")
        remove_button.clicked.connect(self.remove_selected)
        buttons.addWidget(remove_button)
        cancel_button = QPushButton("Отказаться от заказа")
        cancel_button.clicked.connect(self.cancel_order)
        buttons.addWidget(cancel_button)
        buttons.addStretch(1)
        continue_button = QPushButton("Продолжить выбор товаров")
        continue_button.clicked.connect(self.main_window.go_back)
        buttons.addWidget(continue_button)
        self.confirm_button = QPushButton("Подтвердить заказ")
        self.confirm_button.setProperty("primary", True)
        self.confirm_button.clicked.connect(self.confirm_order)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)

    def on_show(self, **kwargs):
        # Менеджер и администратор могут оформить заказ от имени любого клиента
        manage = self.state.can_manage_orders
        self.client_combo.setVisible(manage)
        self.client_label.setVisible(not manage)
        self.client_label.setText(self.state.user_full_name)
        if manage:
            self._load_clients()
        self._fill_table()

    def _load_clients(self):
        try:
            users = get_all_users()
        except AppError as error:
            show_app_error(self, error)
            return
        self.client_combo.clear()
        for user in users:
            name = " ".join(part for part in (user["last_name"], user["first_name"], user["patronymic"]) if part)
            self.client_combo.addItem(name, user["user_id"])
        index = self.client_combo.findData(self.state.user["user_id"])
        self.client_combo.setCurrentIndex(max(index, 0))

    def _fill_table(self):
        cart = self.state.cart
        self.table.setRowCount(len(cart))
        self.amount_items = {}
        for row, item in enumerate(cart):
            name_item = QTableWidgetItem(f"{item['product_name']} ({item['manufacturer_name']})")
            self.table.setItem(row, 0, name_item)
            size_item = QTableWidgetItem(item["size_text"])
            size_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, size_item)

            spin = QSpinBox()
            spin.setRange(1, max(item["max_quantity"], 1))
            spin.setValue(item["quantity"])
            spin.valueChanged.connect(
                lambda value, stock_id=item["stock_item_id"]: self._on_quantity_changed(stock_id, value)
            )
            self.table.setCellWidget(row, 2, spin)

            price_item = QTableWidgetItem(format_price(item["unit_price"]))
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, price_item)
            amount_item = QTableWidgetItem()
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, amount_item)
            self.amount_items[item["stock_item_id"]] = amount_item
        self._update_amounts()

    def _on_quantity_changed(self, stock_item_id, value):
        for item in self.state.cart:
            if item["stock_item_id"] == stock_item_id:
                item["quantity"] = value
        self._update_amounts()

    def _update_amounts(self):
        total = Decimal(0)
        for item in self.state.cart:
            amount = Decimal(item["unit_price"]) * item["quantity"]
            total += amount
            self.amount_items[item["stock_item_id"]].setText(format_price(amount))
        self.total_label.setText(f"Итого к оплате: {format_price(total)}")
        self.confirm_button.setEnabled(bool(self.state.cart))

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            show_warning(self, "Выберите в таблице позицию, которую нужно удалить из заказа.")
            return
        del self.state.cart[row]
        self._fill_table()

    def cancel_order(self):
        if not self.state.cart:
            self.main_window.go_back()
            return
        if ask_confirmation(self, "Отказаться от заказа? Все выбранные позиции будут удалены из заказа."):
            self.state.clear_cart()
            self.main_window.reset_to("catalog")

    def confirm_order(self):
        if not self.state.cart:
            show_warning(self, "В заказе нет ни одной позиции. Выберите товары в каталоге.")
            return
        total = sum(Decimal(item["unit_price"]) * item["quantity"] for item in self.state.cart)
        if not ask_confirmation(self, f"Подтвердить заказ на сумму {format_price(total)}?"):
            return
        if self.state.can_manage_orders:
            user_id = self.client_combo.currentData()
        else:
            user_id = self.state.user["user_id"]
        try:
            order_id = create_order(user_id, self.state.cart)
        except AppError as error:
            show_app_error(self, error)
            return
        self.state.clear_cart()
        show_info(self, f"Заказ №{order_id} оформлен. Спасибо!", "Заказ оформлен")
        self.main_window.reset_to("catalog")
