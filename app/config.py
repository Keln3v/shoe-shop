"""Пути к файлам проекта и чтение параметров подключения из config.ini."""
import configparser
import sys
from pathlib import Path

from app.errors import ConfigError


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_FILE = BASE_DIR / "config.ini"
RESOURCES_DIR = BASE_DIR / "resources"
PRODUCT_IMAGES_DIR = RESOURCES_DIR / "images"
LOGO_FILE = RESOURCES_DIR / "Чудо_Обувь.png"
ICON_FILE = RESOURCES_DIR / "Чудо_Обувь.ico"
PLACEHOLDER_FILE = RESOURCES_DIR / "picture.png"


def load_database_settings():
    """Возвращает параметры подключения к PostgreSQL из секции [database] файла config.ini."""
    if not CONFIG_FILE.exists():
        raise ConfigError(
            "Не найден файл настроек config.ini.\n"
            "Скопируйте config.ini.example в config.ini и укажите параметры подключения к базе данных."
        )
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    if "database" not in config:
        raise ConfigError("В файле config.ini нет раздела [database]. Сверьтесь с config.ini.example.")
    db = config["database"]
    try:
        return {
            "host": db["host"],
            "port": db.getint("port"),
            "dbname": db["name"],
            "user": db["user"],
            "password": db["password"],
        }
    except (KeyError, ValueError) as error:
        raise ConfigError(
            "В разделе [database] файла config.ini заполнены не все параметры или порт указан неверно."
        ) from error
