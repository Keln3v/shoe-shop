from decimal import Decimal

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.catalog_logic import format_pairs, format_price, format_size
from app.database import delete_order_item, get_order, get_order_items, update_order_date
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.messages import ask_confirmation, show_app_error, show_info, show_warning

COLUMNS = ["Модель (наименование, производство)", "Размер", "Количество", "Цена за единицу", "Сумма"]


class OrderDetailsPage(BasePage):
    page_title = "Состав заказа"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.order_id = None
        self.items = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        info = QHBoxLayout()
        self.client_label = QLabel()
        self.client_label.setStyleSheet("font-size: 16px;")
        info.addWidget(self.client_label)
        info.addStretch(1)
        self.date_caption = QLabel("<b>Дата заказа:</b>")
        info.addWidget(self.date_caption)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setMinimumDate(QDate(2000, 1, 1))
        info.addWidget(self.date_edit)
        self.date_label = QLabel()
        info.addWidget(self.date_label)
        self.save_date_button = QPushButton("Сохранить дату")
        self.save_date_button.setProperty("primary", True)
        self.save_date_button.clicked.connect(self.save_date)
        info.addWidget(self.save_date_button)
        layout.addLayout(info)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
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
        self.delete_item_button = QPushButton("Удалить позицию")
        self.delete_item_button.clicked.connect(self.delete_selected_item)
        buttons.addWidget(self.delete_item_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def on_show(self, order_id=None, **kwargs):
        self.order_id = order_id
        # Редактировать заказ (дату, позиции) может только администратор
        is_admin = self.state.is_admin
        self.date_edit.setVisible(is_admin)
        self.save_date_button.setVisible(is_admin)
        self.delete_item_button.setVisible(is_admin)
        self.date_label.setVisible(not is_admin)
        self.page_title = f"Состав заказа №{order_id}"
        try:
            order = get_order(order_id)
            self.items = get_order_items(order_id)
        except AppError as error:
            show_app_error(self, error)
            return
        if order is None:
            show_warning(self, "Заказ не найден: возможно, он уже удалён.")
            return
        self.client_label.setText(f"<b>Клиент:</b> {order['client_name']}")
        order_date = order["order_date"]
        self.date_edit.setDate(QDate(order_date.year, order_date.month, order_date.day))
        self.date_label.setText(order_date.strftime("%d.%m.%Y"))
        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(len(self.items))
        total = Decimal(0)
        for row, item in enumerate(self.items):
            amount = Decimal(item["unit_price"]) * item["quantity"]
            total += amount
            values = [
                f"{item['product_name']} ({item['manufacturer_name']})",
                format_size(item["size_value"]),
                str(item["quantity"]),
                format_price(item["unit_price"]),
                format_price(amount),
            ]
            for column, text in enumerate(values):
                cell = QTableWidgetItem(text)
                if column in (1, 2):
                    cell.setTextAlignment(Qt.AlignCenter)
                elif column in (3, 4):
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, column, cell)
        self.total_label.setText(f"Итоговая сумма по заказу: {format_price(total)}")

    def save_date(self):
        new_date = self.date_edit.date().toPyDate()
        try:
            update_order_date(self.order_id, new_date)
        except AppError as error:
            show_app_error(self, error)
            return
        show_info(self, f"Дата заказа №{self.order_id} изменена на {new_date.strftime('%d.%m.%Y')}.", "Дата сохранена")

    def delete_selected_item(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.items):
            show_warning(self, "Выберите в таблице позицию, которую нужно удалить.")
            return
        item = self.items[row]
        if not ask_confirmation(
            self,
            f"Удалить позицию «{item['product_name']}», размер {format_size(item['size_value'])}, "
            f"{format_pairs(item['quantity'])}?\nТовар вернётся в доступный остаток.",
            "Удаление позиции",
        ):
            return
        try:
            delete_order_item(item["order_item_id"])
        except AppError as error:
            show_app_error(self, error)
            return
        self.on_show(order_id=self.order_id)
        self.main_window.title_label.setText(self.page_title)
