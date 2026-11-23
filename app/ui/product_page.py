from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.catalog_logic import format_pairs, format_price, format_size
from app.database import get_product_sizes
from app.errors import AppError
from app.ui.base_page import BasePage
from app.ui.images import load_product_pixmap
from app.ui.messages import show_app_error, show_info, show_warning

IMAGE_SIZE = 320


class ProductPage(BasePage):
    page_title = "Просмотр товара"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.product = None
        self.sizes = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(28)

        self.image_label = QLabel()
        self.image_label.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label, alignment=Qt.AlignTop)

        right = QVBoxLayout()
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        right.addWidget(self.name_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setVerticalSpacing(8)
        self.value_labels = {}
        for key, caption in (
            ("category", "Категория:"),
            ("manufacturer", "Производство:"),
            ("price", "Цена со скидкой:"),
            ("composition", "Состав:"),
            ("description", "Описание:"),
            ("range", "Размерный ряд:"),
            ("available", "Доступные размеры:"),
        ):
            value = QLabel()
            value.setWordWrap(True)
            value.setTextFormat(Qt.RichText)
            caption_label = QLabel(f"<b>{caption}</b>")
            form.addRow(caption_label, value)
            self.value_labels[key] = value
        right.addLayout(form)
        right.addSpacing(12)

        order_row = QHBoxLayout()
        order_row.addWidget(QLabel("Размер:"))
        self.size_combo = QComboBox()
        self.size_combo.setMinimumWidth(190)
        self.size_combo.currentIndexChanged.connect(self._update_quantity_limit)
        order_row.addWidget(self.size_combo)
        order_row.addSpacing(12)
        order_row.addWidget(QLabel("Количество пар:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        order_row.addWidget(self.quantity_spin)
        order_row.addStretch(1)
        right.addLayout(order_row)

        self.cart_note_label = QLabel()
        self.cart_note_label.setObjectName("hint")
        right.addWidget(self.cart_note_label)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Добавить в заказ")
        self.add_button.setProperty("primary", True)
        self.add_button.clicked.connect(self.add_to_order)
        buttons.addWidget(self.add_button)
        go_cart_button = QPushButton("Перейти к оформлению заказа")
        go_cart_button.clicked.connect(lambda: self.main_window.navigate("cart"))
        buttons.addWidget(go_cart_button)
        buttons.addStretch(1)
        right.addLayout(buttons)
        right.addStretch(1)
        layout.addLayout(right, 1)

    def on_show(self, product=None, **kwargs):
        self.product = product
        try:
            self.sizes = get_product_sizes(product["product_id"])
        except AppError as error:
            self.sizes = []
            show_app_error(self, error)

        self.image_label.setPixmap(load_product_pixmap(product["image_file"], IMAGE_SIZE, IMAGE_SIZE))
        self.name_label.setText(product["product_name"])
        price_text = format_price(product["final_price"])
        if product["has_discount"]:
            price_text = (
                f'<span style="color:#b3261e;"><s>{format_price(product["price"])}</s></span> '
                f"<b>{price_text}</b>"
            )
        else:
            price_text = f"<b>{price_text}</b>"
        available = [item for item in self.sizes if item["quantity"] > 0]
        size_range = "—"
        if self.sizes:
            size_range = f'{format_size(self.sizes[0]["size_value"])} – {format_size(self.sizes[-1]["size_value"])}'
        values = {
            "category": f'{product["category_name"]} / {product["subcategory_name"]}',
            "manufacturer": product["manufacturer_name"],
            "price": price_text,
            "composition": product["composition"],
            "description": product["description"],
            "range": size_range,
            "available": ", ".join(format_size(item["size_value"]) for item in available) or "нет в наличии",
        }
        for key, text in values.items():
            self.value_labels[key].setText(text)

        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        for item in available:
            self.size_combo.addItem(
                f'{format_size(item["size_value"])} (доступно пар: {item["quantity"]})', item
            )
        self.size_combo.blockSignals(False)
        self._update_quantity_limit()

    def _free_quantity(self, size_item):
        """Сколько пар выбранного размера ещё можно добавить с учётом уже собранного заказа."""
        return size_item["quantity"] - self.state.get_cart_quantity(size_item["stock_item_id"])

    def _update_quantity_limit(self, *_):
        size_item = self.size_combo.currentData()
        free = self._free_quantity(size_item) if size_item else 0
        self.quantity_spin.setMaximum(max(free, 1))
        self.quantity_spin.setValue(1)
        self.quantity_spin.setEnabled(free > 0)
        self.add_button.setEnabled(free > 0)
        if size_item is None:
            self.cart_note_label.setText("Этой модели нет в наличии: оформить заказ нельзя.")
        elif free <= 0:
            self.cart_note_label.setText("Все доступные пары этого размера уже добавлены в ваш заказ.")
        else:
            in_cart = self.state.get_cart_quantity(size_item["stock_item_id"])
            self.cart_note_label.setText(f"Уже в заказе: {format_pairs(in_cart)}." if in_cart else "")

    def add_to_order(self):
        size_item = self.size_combo.currentData()
        quantity = self.quantity_spin.value()
        if size_item is None:
            show_warning(self, "Выберите размер, который есть в наличии.")
            return
        if quantity > self._free_quantity(size_item):
            show_warning(
                self,
                f"Доступно для заказа не более {format_pairs(self._free_quantity(size_item))} этого размера. "
                "Уменьшите количество.",
                "Недостаточно товара",
            )
            return
        self.state.add_to_cart(
            {
                "stock_item_id": size_item["stock_item_id"],
                "product_name": self.product["product_name"],
                "manufacturer_name": self.product["manufacturer_name"],
                "size_text": format_size(size_item["size_value"]),
                "quantity": quantity,
                "max_quantity": size_item["quantity"],
                "unit_price": self.product["final_price"],
            }
        )
        self._update_quantity_limit()
        show_info(
            self,
            f"Товар добавлен в заказ: {self.product['product_name']}, размер "
            f"{format_size(size_item['size_value'])}, {format_pairs(quantity)}.\n"
            "Вернитесь в каталог, чтобы выбрать другие модели, или перейдите к оформлению заказа.",
            "Товар добавлен",
        )
