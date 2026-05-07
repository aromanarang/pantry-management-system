from flask import Blueprint, jsonify

from backend.config import get_db


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard-summary", methods=["GET"])
def dashboard_summary():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_ingredients,
            COALESCE(SUM(quantity), 0) AS total_stock_quantity,
            SUM(CASE WHEN quantity < threshold THEN 1 ELSE 0 END) AS low_stock_count
        FROM ingredients
        """
    )
    inventory = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(quantity_sold), 0) AS sales_today,
            COUNT(*) AS sales_entries_today
        FROM sales
        WHERE sale_date = CURDATE()
        """
    )
    sales_today = cursor.fetchone()

    cursor.close()
    db.close()

    return jsonify({
        "inventory": inventory,
        "sales_today": sales_today,
    })


@dashboard_bp.route("/report-insights", methods=["GET"])
def report_insights():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            i.ingredient_name,
            i.unit,
            ROUND(SUM(r.quantity_required * s.quantity_sold), 3) AS total_consumption
        FROM sales s
        JOIN recipes r ON s.menu_id = r.menu_id
        JOIN ingredients i ON i.ingredient_id = r.ingredient_id
        GROUP BY i.ingredient_id, i.ingredient_name, i.unit
        ORDER BY total_consumption DESC, i.ingredient_name ASC
        LIMIT 20
        """
    )
    top_ingredients = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            DATE_FORMAT(s.sale_date, '%%Y-%%m') AS usage_month,
            ROUND(SUM(r.quantity_required * s.quantity_sold), 3) AS total_consumption
        FROM sales s
        JOIN recipes r ON s.menu_id = r.menu_id
        GROUP BY DATE_FORMAT(s.sale_date, '%%Y-%%m')
        ORDER BY usage_month ASC
        """
    )
    monthly_totals = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        "top_ingredients": top_ingredients,
        "monthly_totals": monthly_totals,
    })
