"""Работа с базой данных PostgreSQL: подключение и все запросы приложения."""
from contextlib import contextmanager
from datetime import date

import psycopg2
from psycopg2.extras import RealDictCursor

from app.catalog_logic import DISCOUNT_REFERENCE_DATE, get_previous_month_range
from app.config import load_database_settings
from app.errors import DatabaseConnectionError, DatabaseError, OrderError

CONNECTION_ERROR_MESSAGE = "Не удалось подключиться к базе данных."
QUERY_ERROR_MESSAGE = "Ошибка при выполнении запроса к базе данных. Повторите действие или обратитесь к администратору."


@contextmanager
def open_connection():
    """Открывает соединение; при успехе фиксирует транзакцию, при ошибке откатывает."""
    settings = load_database_settings()
    try:
        connection = psycopg2.connect(connect_timeout=5, **settings)
    except (psycopg2.OperationalError, UnicodeDecodeError) as error:
        raise DatabaseConnectionError(CONNECTION_ERROR_MESSAGE) from error
    try:
        with connection:
            yield connection
    except psycopg2.Error as error:
        raise DatabaseError(QUERY_ERROR_MESSAGE) from error
    finally:
        connection.close()


def fetch_all(sql, params=None):
    with open_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


def get_user_by_login(login):
    rows = fetch_all(
        """
        SELECT u.user_id, u.last_name, u.first_name, u.patronymic, u.login, r.role_name
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        WHERE u.login = %s
        """,
        (login,),
    )
    return rows[0] if rows else None


def get_all_users():
    return fetch_all(
        """
        SELECT user_id, last_name, first_name, patronymic
        FROM users
        ORDER BY last_name, first_name, patronymic
        """
    )


def get_categories():
    return [row["category_name"] for row in fetch_all(
        "SELECT category_name FROM categories ORDER BY category_name"
    )]


def get_catalog():
    """Каталог моделей с суммарным количеством и признаком заказов в прошлом месяце."""
    period_start, period_end = get_previous_month_range(DISCOUNT_REFERENCE_DATE)
    return fetch_all(
        """
        SELECT p.product_id, c.category_name, sc.subcategory_name, p.product_name,
               m.manufacturer_name, p.description, p.composition, p.price, p.image_file,
               COALESCE((SELECT SUM(si.quantity) FROM stock_items si
                         WHERE si.product_id = p.product_id), 0) AS total_quantity,
               EXISTS (SELECT 1
                       FROM order_items oi
                       JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
                       JOIN orders o ON o.order_id = oi.order_id
                       WHERE si.product_id = p.product_id
                         AND o.order_date >= %(period_start)s
                         AND o.order_date < %(period_end)s) AS has_orders_last_month
        FROM products p
        JOIN categories c ON c.category_id = p.category_id
        JOIN subcategories sc ON sc.subcategory_id = p.subcategory_id
        JOIN manufacturers m ON m.manufacturer_id = p.manufacturer_id
        ORDER BY p.product_id
        """,
        {"period_start": period_start, "period_end": period_end},
    )


def get_product_sizes(product_id):
    """Все размеры модели с доступным количеством (включая нулевое)."""
    return fetch_all(
        """
        SELECT si.stock_item_id, s.size_value, si.quantity
        FROM stock_items si
        JOIN sizes s ON s.size_id = si.size_id
        WHERE si.product_id = %s
        ORDER BY s.size_value
        """,
        (product_id,),
    )


def create_order(user_id, cart_items):
    """Оформляет заказ: списывает остатки и сохраняет позиции в одной транзакции."""
    if not cart_items:
        raise OrderError("В заказе нет ни одной товарной позиции. Добавьте товары из каталога.")
    with open_connection() as connection:
        with connection.cursor() as cursor:
            for item in cart_items:
                cursor.execute(
                    """
                    UPDATE stock_items SET quantity = quantity - %s
                    WHERE stock_item_id = %s AND quantity >= %s
                    """,
                    (item["quantity"], item["stock_item_id"], item["quantity"]),
                )
                if cursor.rowcount == 0:
                    raise OrderError(
                        f"Товара «{item['product_name']}» (размер {item['size_text']}) "
                        "осталось меньше, чем указано в заказе. Уменьшите количество или выберите другой размер."
                    )
            cursor.execute(
                "INSERT INTO orders (order_date, user_id) VALUES (%s, %s) RETURNING order_id",
                (date.today(), user_id),
            )
            order_id = cursor.fetchone()[0]
            for item in cart_items:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, stock_item_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, item["stock_item_id"], item["quantity"], item["unit_price"]),
                )
    return order_id


def get_orders():
    return fetch_all(
        """
        SELECT o.order_id, o.order_date,
               concat_ws(' ', u.last_name, u.first_name, u.patronymic) AS client_name,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_amount
        FROM orders o
        JOIN users u ON u.user_id = o.user_id
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, o.order_date, u.last_name, u.first_name, u.patronymic
        ORDER BY o.order_date DESC, o.order_id DESC
        """
    )


def get_order(order_id):
    rows = fetch_all(
        """
        SELECT o.order_id, o.order_date,
               concat_ws(' ', u.last_name, u.first_name, u.patronymic) AS client_name
        FROM orders o
        JOIN users u ON u.user_id = o.user_id
        WHERE o.order_id = %s
        """,
        (order_id,),
    )
    return rows[0] if rows else None


def get_order_items(order_id):
    return fetch_all(
        """
        SELECT oi.order_item_id, p.product_name, m.manufacturer_name, s.size_value,
               oi.quantity, oi.unit_price
        FROM order_items oi
        JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
        JOIN products p ON p.product_id = si.product_id
        JOIN manufacturers m ON m.manufacturer_id = p.manufacturer_id
        JOIN sizes s ON s.size_id = si.size_id
        WHERE oi.order_id = %s
        ORDER BY oi.order_item_id
        """,
        (order_id,),
    )


def delete_order(order_id):
    """Удаляет заказ и возвращает его товары в доступный остаток."""
    with open_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE stock_items si SET quantity = si.quantity + oi.quantity
                FROM order_items oi
                WHERE oi.order_id = %s AND oi.stock_item_id = si.stock_item_id
                """,
                (order_id,),
            )
            cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))


def update_order_date(order_id, new_date):
    with open_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE orders SET order_date = %s WHERE order_id = %s", (new_date, order_id))


def delete_order_item(order_item_id):
    """Удаляет позицию заказа и возвращает товар в остаток. Последнюю позицию удалить нельзя."""
    with open_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT order_id, stock_item_id, quantity FROM order_items WHERE order_item_id = %s",
                (order_item_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise OrderError("Позиция заказа не найдена: возможно, она уже удалена. Обновите список.")
            order_id, stock_item_id, quantity = row
            cursor.execute("SELECT COUNT(*) FROM order_items WHERE order_id = %s", (order_id,))
            if cursor.fetchone()[0] <= 1:
                raise OrderError(
                    "Нельзя удалить единственную позицию заказа. "
                    "Чтобы убрать заказ целиком, удалите его в списке заказов."
                )
            cursor.execute(
                "UPDATE stock_items SET quantity = quantity + %s WHERE stock_item_id = %s",
                (quantity, stock_item_id),
            )
            cursor.execute("DELETE FROM order_items WHERE order_item_id = %s", (order_item_id,))
