"""Бизнес-логика каталога: цена со скидкой, надпись о количестве, поиск, фильтр и сортировка."""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

DISCOUNT_PERCENT = 25
# Дата, относительно которой определяется «предыдущий календарный месяц» для скидки
DISCOUNT_REFERENCE_DATE = date(2026, 5, 15)

SORT_NONE = "Без сортировки"
SORT_PRICE_ASC = "Цена: по возрастанию"
SORT_PRICE_DESC = "Цена: по убыванию"
ALL_CATEGORIES = "Все категории"
MANY_THRESHOLD = 5


def get_previous_month_range(reference_date):
    """Границы предыдущего календарного месяца: [начало, начало следующего месяца)."""
    first_day_of_current_month = reference_date.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    return last_day_of_previous_month.replace(day=1), first_day_of_current_month


def calculate_price_with_discount(price, has_orders_last_month):
    """Цена в рублях: скидка 25% на товары, по которым не было заказов в прошлом месяце."""
    price = Decimal(price)
    if has_orders_last_month:
        return price
    discount_multiplier = Decimal(100 - DISCOUNT_PERCENT) / Decimal(100)
    return (price * discount_multiplier).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def get_stock_label(total_quantity):
    return "Много в наличии" if total_quantity > MANY_THRESHOLD else "Мало в наличии"


def is_low_stock(total_quantity):
    return total_quantity <= 3


def prepare_catalog(rows):
    """Добавляет к строкам каталога цену со скидкой и признак наличия скидки."""
    products = []
    for row in rows:
        product = dict(row)
        product["final_price"] = calculate_price_with_discount(
            product["price"], product["has_orders_last_month"]
        )
        product["has_discount"] = product["final_price"] < Decimal(product["price"])
        products.append(product)
    return products


def filter_and_sort_products(products, search_text, category_name, sort_mode):
    """Поиск (по наименованию и описанию) и фильтр по категории применяются совместно."""
    search_text = search_text.strip().casefold()
    result = []
    for product in products:
        if (
            category_name != ALL_CATEGORIES
            and product["category_name"] != category_name
        ):
            continue
        if search_text:
            haystack = (
                product["product_name"] + " " + product["description"]
            ).casefold()
            if search_text not in haystack:
                continue
        result.append(product)
    if sort_mode == SORT_PRICE_ASC:
        result.sort(key=lambda item: item["final_price"])
    elif sort_mode == SORT_PRICE_DESC:
        result.sort(key=lambda item: item["final_price"], reverse=True)
    return result


def format_price(value):
    text = f"{Decimal(value):,.2f}".replace(",", " ").replace(".", ",")
    if text.endswith(",00"):
        text = text[:-3]
    return f"{text} руб."


def format_size(size_value):
    return f"{float(size_value):g}"


def format_pairs(count):
    """Число с правильным склонением слова «пара»: 1 пара, 2 пары, 5 пар."""
    if 11 <= count % 100 <= 14:
        word = "пар"
    elif count % 10 == 1:
        word = "пара"
    elif 2 <= count % 10 <= 4:
        word = "пары"
    else:
        word = "пар"
    return f"{count} {word}"
