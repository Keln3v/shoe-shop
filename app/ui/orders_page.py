from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.catalog_logic import format_price
from app.database import delete_order, get_orders
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.messages import ask_confirmation, show_app_error, show_info, show_warning

COLUMNS = ["№ заказа", "Дата заказа", "ФИО клиента", "Сумма заказа"]


class OrdersPage(BasePage):
    page_title = "Список заказов"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.orders = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for column in (0, 1, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.table.doubleClicked.connect(self.open_details)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        details_button = QPushButton("Состав заказа")
        details_button.clicked.connect(self.open_details)
        buttons.addWidget(details_button)
        delete_button = QPushButton("Удалить заказ")
        delete_button.clicked.connect(self.delete_selected)
        buttons.addWidget(delete_button)
        buttons.addStretch(1)
        add_button = QPushButton("Добавить заказ")
        add_button.setProperty("primary", True)
        add_button.clicked.connect(self.add_order)
        buttons.addWidget(add_button)
        layout.addLayout(buttons)

    def on_show(self, **kwargs):
        try:
            self.orders = get_orders()
        except AppError as error:
            self.orders = []
            show_app_error(self, error)
        self.table.setRowCount(len(self.orders))
        for row, order in enumerate(self.orders):
            values = [
                str(order["order_id"]),
                order["order_date"].strftime("%d.%m.%Y"),
                order["client_name"],
                format_price(order["total_amount"]),
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column in (0, 1):
                    item.setTextAlignment(Qt.AlignCenter)
                elif column == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, column, item)

    def _selected_order(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.orders):
            show_warning(self, "Выберите заказ в списке.")
            return None
        return self.orders[row]

    def open_details(self, *_):
        order = self._selected_order()
        if order:
            self.main_window.navigate("order_details", order_id=order["order_id"])

    def add_order(self):
        # Товары выбираются в каталоге (с поиском по наименованию), затем оформляется заказ
        self.main_window.navigate("catalog")

    def delete_selected(self):
        order = self._selected_order()
        if not order:
            return
        if not ask_confirmation(
            self,
            f"Удалить заказ №{order['order_id']} ({order['client_name']})?\n"
            "Операция необратима. Товары из заказа вернутся в доступный остаток.",
            "Удаление заказа",
        ):
            return
        try:
            delete_order(order["order_id"])
        except AppError as error:
            show_app_error(self, error)
            return
        show_info(self, f"Заказ №{order['order_id']} удалён.", "Заказ удалён")
        self.on_show()
