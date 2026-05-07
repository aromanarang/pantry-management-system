from flask import Blueprint, jsonify, request
from backend.config import get_db
from backend.services.inventory_service import increase_stock
from backend.services.matching_service import match_ingredient
from backend.services.unit_conversion_service import normalize_quantity_to_db_unit

pantry_bp = Blueprint("pantry", __name__)

@pantry_bp.route("/pantry", methods=["GET"])
def get_pantry():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM ingredients ORDER BY ingredient_name ASC")

    items = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(items)


@pantry_bp.route("/low-stock", methods=["GET"])
def low_stock():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM ingredients WHERE quantity < threshold"
    )

    items = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(items)


@pantry_bp.route("/add-stock", methods=["POST"])
def add_stock():

    data = request.get_json(silent=True) or {}

    ingredient_name = data.get("ingredient_name")
    quantity = data.get("quantity")
    unit = data.get("unit")

    if ingredient_name is None or quantity is None:
        return jsonify({"error": "ingredient_name and quantity are required"}), 400

    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return jsonify({"error": "quantity must be a valid number"}), 400

    if quantity <= 0:
        return jsonify({"error": "quantity must be greater than 0"}), 400

    matched_name = match_ingredient(ingredient_name, score_cutoff=50)

    if not matched_name:
        return jsonify({"error": "ingredient not found"}), 404

    try:
        normalized = normalize_quantity_to_db_unit(
            ingredient_name=matched_name,
            quantity=quantity,
            source_unit=unit,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    increase_stock(matched_name, normalized["converted_quantity"])

    return jsonify({
        "message": "Stock added successfully",
        "ingredient_name": matched_name,
        "quantity_received": quantity,
        "received_unit": normalized["source_unit"],
        "quantity_added": normalized["converted_quantity"],
        "stored_unit": normalized["target_unit"],
    })
