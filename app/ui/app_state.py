from app.constants import ROLE_ADMIN, ROLE_MANAGER


class AppState:
    """Текущий пользователь и корзина (заказ в процессе формирования)."""

    def __init__(self):
        self.user = None
        self.cart = []

    @property
    def is_authorized(self):
        return self.user is not None

    @property
    def is_admin(self):
        return self.is_authorized and self.user["role_name"] == ROLE_ADMIN

    @property
    def can_manage_orders(self):
        return self.is_authorized and self.user["role_name"] in (ROLE_ADMIN, ROLE_MANAGER)

    @property
    def user_full_name(self):
        if not self.is_authorized:
            return "Гость"
        parts = (self.user["last_name"], self.user["first_name"], self.user["patronymic"])
        return " ".join(part for part in parts if part)

    def get_cart_quantity(self, stock_item_id):
        for item in self.cart:
            if item["stock_item_id"] == stock_item_id:
                return item["quantity"]
        return 0

    def add_to_cart(self, new_item):
        for item in self.cart:
            if item["stock_item_id"] == new_item["stock_item_id"]:
                item["quantity"] += new_item["quantity"]
                item["max_quantity"] = new_item["max_quantity"]
                return
        self.cart.append(dict(new_item))

    def clear_cart(self):
        self.cart = []

    def logout(self):
        self.user = None
        self.clear_cart()
