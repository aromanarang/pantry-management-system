from backend.config import get_db


def increase_stock(ingredient_name, quantity):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE ingredients SET quantity = quantity + %s WHERE ingredient_name=%s",
        (quantity, ingredient_name)
    )

    db.commit()

    cursor.close()
    db.close()


def increase_stock_with_cursor(cursor, ingredient_name, quantity):

    cursor.execute(
        "UPDATE ingredients SET quantity = quantity + %s WHERE ingredient_name=%s",
        (quantity, ingredient_name)
    )


def check_ingredient_availability(menu_id, quantity_sold, cursor=None):
    owns_connection = cursor is None

    if owns_connection:
        db = get_db()
        cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            i.ingredient_id,
            i.ingredient_name,
            i.quantity AS current_quantity,
            r.quantity_required
        FROM recipes r
        JOIN ingredients i ON i.ingredient_id = r.ingredient_id
        WHERE r.menu_id=%s
        """,
        (menu_id,)
    )

    recipes = cursor.fetchall()
    shortages = []

    for recipe in recipes:
        ingredient_id, ingredient_name, current_quantity, quantity_required = recipe
        required_quantity = quantity_required * quantity_sold

        if current_quantity < required_quantity:
            shortages.append({
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient_name,
                "required_quantity": required_quantity,
                "available_quantity": current_quantity,
            })

    if owns_connection:
        cursor.close()
        db.close()

    return shortages


def deduct_ingredients(menu_id, quantity_sold, cursor=None):
    owns_connection = cursor is None

    if owns_connection:
        db = get_db()
        cursor = db.cursor()

    shortages = check_ingredient_availability(menu_id, quantity_sold, cursor=cursor)

    if shortages:
        ingredient_names = ", ".join(item["ingredient_name"] for item in shortages)

        if owns_connection:
            cursor.close()
            db.close()

        raise ValueError(f"Insufficient stock for: {ingredient_names}")

    cursor.execute(
        "SELECT ingredient_id, quantity_required FROM recipes WHERE menu_id=%s",
        (menu_id,)
    )

    recipes = cursor.fetchall()

    for recipe in recipes:
        ingredient_id, quantity_required = recipe
        used = quantity_required * quantity_sold

        cursor.execute(
            "UPDATE ingredients SET quantity = quantity - %s WHERE ingredient_id=%s",
            (used, ingredient_id)
        )

    if owns_connection:
        db.commit()
        cursor.close()
        db.close()
