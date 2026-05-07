from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.config import get_db
from backend.services.inventory_service import check_ingredient_availability, deduct_ingredients
from backend.services.matching_service import match_menu_item
from backend.services.sales_import_service import parse_sales_summary_csv


sales_bp = Blueprint("sales", __name__)

UPLOAD_FOLDER = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


@sales_bp.route("/import-sales-summary", methods=["POST"])
def import_sales_summary():

    if "report" not in request.files:
        return jsonify({"error": "report file is required"}), 400

    file = request.files["report"]

    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({"error": "invalid filename"}), 400

    path = UPLOAD_FOLDER / f"{uuid4().hex}_{filename}"
    file.save(path)
    file.stream.seek(0)

    try:
        imported_items = parse_sales_summary_csv(file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        dish_totals = {}
        unmatched_items = []

        for item in imported_items:
            matched_dish = match_menu_item(item["name"])

            if not matched_dish:
                unmatched_items.append(item)
                continue

            dish_totals[matched_dish] = dish_totals.get(matched_dish, 0) + int(item["quantity"])

        processed_sales = []
        stock_errors = []

        for menu_name, quantity_sold in dish_totals.items():
            cursor.execute(
                "SELECT menu_id FROM menu_items WHERE menu_name=%s",
                (menu_name,),
            )

            result = cursor.fetchone()

            if not result:
                unmatched_items.append({"name": menu_name, "quantity": quantity_sold})
                continue

            menu_id = result[0]

            shortages = check_ingredient_availability(menu_id, quantity_sold, cursor=cursor)

            if shortages:
                stock_errors.append({
                    "menu_name": menu_name,
                    "quantity_sold": quantity_sold,
                    "reason": "Insufficient stock",
                    "ingredients": shortages,
                })
                continue

            try:
                cursor.execute("SAVEPOINT sales_item")
                cursor.execute(
                    "INSERT INTO sales (menu_id,quantity_sold,sale_date) VALUES (%s,%s,CURDATE())",
                    (menu_id, quantity_sold),
                )
                deduct_ingredients(menu_id, quantity_sold, cursor=cursor)
            except ValueError as exc:
                cursor.execute("ROLLBACK TO SAVEPOINT sales_item")
                stock_errors.append({
                    "menu_name": menu_name,
                    "quantity_sold": quantity_sold,
                    "reason": str(exc),
                })
                continue

            processed_sales.append({
                "menu_name": menu_name,
                "quantity_sold": quantity_sold,
            })

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()

    return jsonify({
        "message": "Day-end sales summary processed",
        "processed_sales": processed_sales,
        "unmatched_items": unmatched_items,
        "stock_errors": stock_errors,
    })
