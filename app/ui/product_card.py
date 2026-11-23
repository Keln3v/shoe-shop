"""Карточка модели обуви в списке каталога."""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.catalog_logic import format_price, get_stock_label, is_low_stock
from app.constants import COLOR_LOW_STOCK
from app.ui.images import load_product_pixmap

IMAGE_SIZE = 150


class ProductCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, product, clickable):
        super().__init__()
        self.product = product
        self.clickable = clickable
        self.setObjectName("productCard")
        self.setFixedHeight(IMAGE_SIZE + 24)
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
        # Товары с малым остатком подсвечиваются цветом из руководства по стилю
        if is_low_stock(product["total_quantity"]):
            self.setStyleSheet(
                f"QFrame#productCard {{ background: {COLOR_LOW_STOCK}; border: 1px solid #c95a5a; border-radius: 6px; }}"
            )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)

        image = QLabel()
        image.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
        image.setAlignment(Qt.AlignCenter)
        image.setPixmap(load_product_pixmap(product["image_file"], IMAGE_SIZE, IMAGE_SIZE))
        layout.addWidget(image)

        info = QVBoxLayout()
        title = QLabel(f"{product['category_name']} | {product['product_name']}")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 17px; font-weight: bold;")
        info.addWidget(title)
        for text in (
            f"Производство: {product['manufacturer_name']}",
            f"Состав: {product['composition']}",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            info.addWidget(label)
        info.addStretch(1)
        layout.addLayout(info, 1)

        side = QVBoxLayout()
        side.addWidget(QLabel("Цена:"), alignment=Qt.AlignRight)
        side.addWidget(self._build_price_label(product), alignment=Qt.AlignRight)
        side.addStretch(1)
        side.addWidget(QLabel("Количество пар:"), alignment=Qt.AlignRight)
        quantity = QLabel(get_stock_label(product["total_quantity"]))
        quantity.setStyleSheet("font-size: 17px; font-weight: bold;")
        side.addWidget(quantity, alignment=Qt.AlignRight)
        layout.addLayout(side)
        side_widget_width = 190
        for index in range(side.count()):
            widget = side.itemAt(index).widget()
            if widget:
                widget.setMinimumWidth(side_widget_width)
                widget.setAlignment(Qt.AlignRight)

    @staticmethod
    def _build_price_label(product):
        label = QLabel()
        label.setTextFormat(Qt.RichText)
        new_price = format_price(product["final_price"])
        if product["has_discount"]:
            old_price = format_price(product["price"])
            label.setText(
                f'<span style="color:#b3261e;"><s>{old_price}</s></span><br>'
                f'<span style="font-size:18px; font-weight:bold;">{new_price}</span>'
            )
        else:
            label.setText(f'<span style="font-size:18px; font-weight:bold;">{new_price}</span>')
        return label

    def mouseReleaseEvent(self, event):
        if self.clickable and event.button() == Qt.LeftButton:
            self.clicked.emit(self.product)
        super().mouseReleaseEvent(event)
