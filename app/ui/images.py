"""Загрузка изображений товаров; при отсутствии файла выводится заглушка picture.png."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from app.config import PLACEHOLDER_FILE, PRODUCT_IMAGES_DIR

_cache = {}


def load_product_pixmap(image_file, width, height):
    key = (image_file, width, height)
    if key not in _cache:
        pixmap = QPixmap()
        if image_file:
            pixmap = QPixmap(str(PRODUCT_IMAGES_DIR / image_file))
        if pixmap.isNull():
            pixmap = QPixmap(str(PLACEHOLDER_FILE))
        _cache[key] = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return _cache[key]
