import csv
from io import StringIO


POSSIBLE_NAME_COLUMNS = [
    "menu_name",
    "dish_name",
    "item_name",
    "item",
    "product_name",
    "product",
]

POSSIBLE_QUANTITY_COLUMNS = [
    "quantity_sold",
    "quantity",
    "qty",
    "count",
    "items_sold",
]


def _pick_column(fieldnames, candidates):
    if not fieldnames:
        return None

    normalized_to_original = {name.strip().lower(): name for name in fieldnames if name}

    for candidate in candidates:
        if candidate in normalized_to_original:
            return normalized_to_original[candidate]

    return None


def parse_sales_summary_csv(file_storage):
    raw_text = file_storage.stream.read().decode("utf-8-sig")
    file_storage.stream.seek(0)

    reader = csv.DictReader(StringIO(raw_text))

    if not reader.fieldnames:
        raise ValueError("CSV file must include a header row")

    name_column = _pick_column(reader.fieldnames, POSSIBLE_NAME_COLUMNS)
    quantity_column = _pick_column(reader.fieldnames, POSSIBLE_QUANTITY_COLUMNS)

    if not name_column or not quantity_column:
        raise ValueError(
            "CSV must contain menu name and quantity columns such as menu_name and quantity_sold"
        )

    items = []

    for index, row in enumerate(reader, start=2):
        raw_name = (row.get(name_column) or "").strip()
        raw_quantity = (row.get(quantity_column) or "").strip()

        if not raw_name:
            continue

        if not raw_quantity:
            raise ValueError(f"Missing quantity in row {index}")

        try:
            quantity = int(float(raw_quantity))
        except ValueError as exc:
            raise ValueError(f"Invalid quantity '{raw_quantity}' in row {index}") from exc

        if quantity <= 0:
            continue

        items.append({
            "name": raw_name,
            "quantity": quantity,
        })

    return items
