from flask import Blueprint, request, jsonify
from pathlib import Path
from uuid import uuid4

import pytesseract
from werkzeug.utils import secure_filename

from backend.config import get_db
from backend.services.inventory_service import increase_stock_with_cursor
from backend.services.matching_service import match_ingredient
from backend.services.ocr_service import extract_items
from backend.services.unit_conversion_service import normalize_quantity_to_db_unit

bill_bp = Blueprint("bill", __name__)

UPLOAD_FOLDER = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


@bill_bp.route("/upload-bill", methods=["POST"])
def upload_bill():

    if "bill" not in request.files:
        return jsonify({"error": "bill file is required"}), 400

    file = request.files["bill"]

    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({"error": "invalid filename"}), 400

    path = UPLOAD_FOLDER / f"{uuid4().hex}_{filename}"
    file.save(path)

    try:
        extraction = extract_items(str(path))
    except pytesseract.pytesseract.TesseractNotFoundError:
        return jsonify({
            "error": "Tesseract OCR is not installed or not configured correctly"
        }), 500
    except RuntimeError as exc:
        return jsonify({
            "error": f"OCR setup error: {exc}"
        }), 500

    if extraction["bill_type"] != "grocery":
        return jsonify({
            "error": "uploaded file looks like a restaurant bill, not a grocery bill"
        }), 400

    items = extraction["items"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO purchase_bills (supplier_name,bill_date) VALUES (%s,CURDATE())",
        ("Unknown",)
    )

    bill_id = cursor.lastrowid
    processed_items = []
    unmatched_items = []

    for item in items:
        ingredient_name = match_ingredient(item["name"])

        if not ingredient_name:
            unmatched_items.append(item)
            continue

        try:
            normalized = normalize_quantity_to_db_unit(
                ingredient_name=ingredient_name,
                quantity=item["quantity"],
                source_unit=item.get("unit"),
            )
        except ValueError as exc:
            unmatched_items.append({
                "name": item["name"],
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "reason": str(exc),
            })
            continue

        cursor.execute(
            "SELECT ingredient_id FROM ingredients WHERE ingredient_name=%s",
            (ingredient_name,)
        )

        result = cursor.fetchone()

        if result:

            ingredient_id = result[0]

            cursor.execute(
                "INSERT INTO bill_items (bill_id,ingredient_id,quantity) VALUES (%s,%s,%s)",
                (bill_id, ingredient_id, normalized["converted_quantity"])
            )

            increase_stock_with_cursor(cursor, ingredient_name, normalized["converted_quantity"])
            processed_items.append({
                "original_name": item["name"],
                "matched_name": ingredient_name,
                "quantity_received": float(item["quantity"]),
                "received_unit": normalized["source_unit"],
                "quantity_added": normalized["converted_quantity"],
                "stored_unit": normalized["target_unit"],
            })

    db.commit()
    cursor.close()
    db.close()

    return jsonify({
        "message": "Grocery bill processed",
        "bill_id": bill_id,
        "processed_items": processed_items,
        "unmatched_items": unmatched_items,
    })
