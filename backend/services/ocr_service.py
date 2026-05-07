import os
import re

import cv2
import pandas as pd
import pytesseract


def _resolve_tesseract_path():
    candidates = [
        os.getenv("TESSERACT_PATH"),
        r"C:\Users\aroma\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return candidates[1]


pytesseract.pytesseract.tesseract_cmd = _resolve_tesseract_path()
_tesseract_dir = os.path.dirname(pytesseract.pytesseract.tesseract_cmd)
_tessdata_dir = os.path.join(_tesseract_dir, "tessdata")

if os.path.isdir(_tessdata_dir):
    os.environ["TESSDATA_PREFIX"] = _tessdata_dir

NOISE_WORDS = {
    "gst",
    "cgst",
    "sgst",
    "tax",
    "invoice",
    "bill",
    "subtotal",
    "sub total",
    "grand total",
    "amount",
    "cash",
    "change",
    "discount",
    "total",
    "move to wishlist",
    "wishlist",
    "move to",
    "invoice",
    "bill no",
    "payment mode",
    "thank you for shopping with us",
    "visit again",
    "grand total",
    "subtotal",
    "total items",
}

UNIT_PATTERN = r"(kg|g|l|ml|litre|liter|pcs|pc|pack|unit)"
INVOICE_UNIT_PATTERN = r"(kg|g|l|ml|litre|liter|pcs|pc|pack|unit|\|)"


def preprocess_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    return cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )


def preprocess_invoice_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    inverted = cv2.bitwise_not(enlarged)

    binary = cv2.adaptiveThreshold(
        inverted,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        15,
        -2,
    )

    horizontal = binary.copy()
    vertical = binary.copy()

    horizontal_size = max(1, horizontal.shape[1] // 30)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal = cv2.erode(horizontal, horizontal_kernel)
    horizontal = cv2.dilate(horizontal, horizontal_kernel)

    vertical_size = max(1, vertical.shape[0] // 30)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
    vertical = cv2.erode(vertical, vertical_kernel)
    vertical = cv2.dilate(vertical, vertical_kernel)

    table_lines = cv2.add(horizontal, vertical)
    return cv2.bitwise_not(cv2.subtract(inverted, table_lines))


def extract_ocr_dataframe(image_path, psm=6, invoice_mode=False):
    processed = preprocess_invoice_image(image_path) if invoice_mode else preprocess_image(image_path)

    dataframe = pytesseract.image_to_data(
        processed,
        output_type=pytesseract.Output.DATAFRAME,
        config=f"--oem 3 --psm {psm}",
    )

    dataframe = dataframe.dropna(subset=["text", "conf"])
    dataframe["text"] = dataframe["text"].astype(str).str.strip()
    dataframe = dataframe[dataframe["text"] != ""]
    dataframe["conf"] = pd.to_numeric(dataframe["conf"], errors="coerce").fillna(-1)

    return dataframe[dataframe["conf"] >= 20]


def reconstruct_lines(dataframe, row_gap=12):
    if dataframe.empty:
        return []

    dataframe = dataframe.sort_values(by=["top", "left"])
    rows = []
    current_row = []
    last_top = None

    for _, row in dataframe.iterrows():
        top = int(row["top"])

        if last_top is None or abs(top - last_top) <= row_gap:
            current_row.append(row)
        else:
            rows.append(current_row)
            current_row = [row]

        last_top = top

    if current_row:
        rows.append(current_row)

    lines = []

    for row in rows:
        ordered_words = sorted(row, key=lambda item: int(item["left"]))
        text = " ".join(str(word["text"]) for word in ordered_words).strip()

        if text:
            lines.append(text)

    return lines


def build_text_blocks(dataframe, row_gap=18):
    if dataframe.empty:
        return []

    dataframe = dataframe.sort_values(by=["top", "left"])
    rows = []
    current_row = []
    last_top = None

    for _, row in dataframe.iterrows():
        top = int(row["top"])

        if last_top is None or abs(top - last_top) <= row_gap:
            current_row.append(row)
        else:
            rows.append(current_row)
            current_row = [row]

        last_top = top

    if current_row:
        rows.append(current_row)

    blocks = []

    for row in rows:
        ordered_words = sorted(row, key=lambda item: int(item["left"]))
        text = " ".join(str(word["text"]) for word in ordered_words).strip()

        if not text:
            continue

        left = min(int(word["left"]) for word in ordered_words)
        top = min(int(word["top"]) for word in ordered_words)
        width = max(int(word["left"]) + int(word["width"]) for word in ordered_words) - left
        height = max(int(word["top"]) + int(word["height"]) for word in ordered_words) - top

        blocks.append({
            "text": text,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        })

    return blocks


def is_noise(line):
    lowered = line.lower().strip()
    return any(word in lowered for word in NOISE_WORDS)


def is_meaningful_product_text(text):
    cleaned = text.strip()

    if not cleaned or is_noise(cleaned):
        return False

    alpha_words = re.findall(r"[A-Za-z]{2,}", cleaned)
    alpha_chars = re.findall(r"[A-Za-z]", cleaned)

    if len(alpha_chars) < 4:
        return False

    if not alpha_words:
        return False

    return any(len(word) >= 3 for word in alpha_words)


def is_quantity_text(text):
    return bool(re.search(rf"\b\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", text.lower()))


def classify_bill(lines):
    grocery_score = 0
    restaurant_score = 0

    for line in lines:
        lowered = line.lower()

        if is_noise(line):
            continue

        if any(token in lowered for token in ["item price quantity unit", "quantity unit", "fresh groceries"]):
            grocery_score += 3

        if re.search(rf"[a-z][a-z\s\-\(\)]+?\s+\d+(?:\.\d+)?\s+\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", lowered):
            grocery_score += 3

        if re.search(rf"\b\d+\s*x\s*\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", lowered):
            grocery_score += 2
        elif re.search(rf"\b\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", lowered):
            grocery_score += 1

        if re.search(r"(?:rs\.?\s*)?\d+(?:\.\d+)?\s+0*\d+\b", lowered):
            restaurant_score += 2
        elif re.search(r"\bx\s*\d+\b", lowered):
            restaurant_score += 1

    return "grocery" if grocery_score >= restaurant_score else "restaurant"


def _extract_quantity_and_unit(text):
    lowered = text.lower().replace(" |", " l").replace("|", " l ")

    multiplied_match = re.search(
        rf"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*{UNIT_PATTERN}\b",
        lowered,
    )
    simple_match = re.search(
        rf"(\d+(?:\.\d+)?)\s*{UNIT_PATTERN}\b",
        lowered,
    )

    if multiplied_match:
        return (
            float(multiplied_match.group(1)) * float(multiplied_match.group(2)),
            multiplied_match.group(3).lower(),
        )

    if simple_match:
        return float(simple_match.group(1)), simple_match.group(2).lower()

    return None, None


def _normalize_extracted_unit(unit):
    if unit == "|":
        return "l"
    return unit.lower()


def _clean_product_name(text):
    cleaned = re.sub(rf"\b\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" -:.[]()")
    return cleaned


def parse_grocery_blocks(blocks):
    quantity_blocks = []
    product_blocks = []

    for block in blocks:
        text = block["text"].strip()

        if is_noise(text):
            continue

        quantity, unit = _extract_quantity_and_unit(text)

        if quantity is not None:
            quantity_blocks.append({
                **block,
                "quantity": quantity,
                "unit": unit,
            })
            continue

        cleaned_name = _clean_product_name(text)

        if is_meaningful_product_text(cleaned_name):
            product_blocks.append({
                **block,
                "name": cleaned_name,
            })

    items = []
    used_product_keys = set()

    for quantity_block in quantity_blocks:
        best_product = None
        best_score = None

        for product_block in product_blocks:
            vertical_gap = quantity_block["top"] - product_block["top"]

            if vertical_gap < -60 or vertical_gap > 170:
                continue

            horizontal_gap = abs(quantity_block["left"] - product_block["left"])
            score = abs(vertical_gap) + (horizontal_gap * 0.35)

            if best_score is None or score < best_score:
                best_score = score
                best_product = product_block

        if best_product:
            product_key = (best_product["name"], best_product["top"], best_product["left"])

            if product_key in used_product_keys:
                continue

            used_product_keys.add(product_key)
            items.append({
                "name": best_product["name"],
                "quantity": quantity_block["quantity"],
                "unit": quantity_block["unit"],
            })

    return items


def parse_grocery_lines(lines):
    items = []

    for index, line in enumerate(lines):
        if is_noise(line):
            continue

        normalized_line = line.replace("|", " l ")

        table_match = re.search(
            rf"(.+?)\s+\d+(?:\.\d+)?\s+(\d+(?:\.\d+)?)\s*({UNIT_PATTERN})\b",
            normalized_line,
            re.IGNORECASE,
        )

        if table_match:
            name = _clean_product_name(table_match.group(1))
            quantity = float(table_match.group(2))
            unit = table_match.group(3).lower()

            if name and is_meaningful_product_text(name):
                items.append({
                    "name": name,
                    "quantity": quantity,
                    "unit": unit,
                })
                continue

        table_without_unit_match = re.search(
            r"(.+?)\s+\d+(?:\.\d+)?\s+(\d+(?:\.\d+)?)\b",
            line,
            re.IGNORECASE,
        )

        if table_without_unit_match:
            name = _clean_product_name(table_without_unit_match.group(1))
            quantity = float(table_without_unit_match.group(2))

            if name and is_meaningful_product_text(name):
                items.append({
                    "name": name,
                    "quantity": quantity,
                    "unit": None,
                })
                continue

        quantity, unit = _extract_quantity_and_unit(line)

        if quantity is None:
            continue

        current_without_qty = _clean_product_name(line)

        if current_without_qty and is_meaningful_product_text(current_without_qty):
            name = current_without_qty
        else:
            name = None

            for previous_index in range(index - 1, -1, -1):
                candidate = _clean_product_name(lines[previous_index])

                if candidate and is_meaningful_product_text(candidate) and not is_quantity_text(candidate):
                    name = candidate
                    break

        if name:
            items.append({
                "name": name,
                "quantity": quantity,
                "unit": unit,
            })

    return items


def parse_restaurant_lines(lines):
    items = []

    for line in lines:
        if is_noise(line):
            continue

        column_match = re.search(
            r"(.+?)\s+(?:rs\.?\s*)?\d+(?:\.\d+)?\s+0*(\d+)\b",
            line,
            re.IGNORECASE,
        )
        inline_match = re.search(r"(.+?)\s+\bx\s*0*(\d+)\b", line, re.IGNORECASE)

        if column_match:
            items.append({
                "name": column_match.group(1).strip(),
                "quantity": int(column_match.group(2)),
            })
            continue

        if inline_match:
            items.append({
                "name": inline_match.group(1).strip(),
                "quantity": int(inline_match.group(2)),
            })
            continue

        stripped = line.strip()
        if len(stripped.split()) > 1:
            items.append({
                "name": stripped,
                "quantity": 1,
            })

    return items


def _deduplicate_items(items):
    unique = []
    seen = set()

    for item in items:
        key = (
            item["name"].strip().lower(),
            float(item["quantity"]),
            (item["unit"] or "").strip().lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def extract_items(image_path):
    dense_dataframe = extract_ocr_dataframe(image_path, psm=6)
    dense_lines = reconstruct_lines(dense_dataframe, row_gap=12)
    bill_type = classify_bill(dense_lines)

    if bill_type == "grocery":
        sparse_dataframe = extract_ocr_dataframe(image_path, psm=11)
        sparse_lines = reconstruct_lines(sparse_dataframe, row_gap=18)
        sparse_blocks = build_text_blocks(sparse_dataframe, row_gap=18)
        invoice_dataframe = extract_ocr_dataframe(image_path, psm=6, invoice_mode=True)
        invoice_lines = reconstruct_lines(invoice_dataframe, row_gap=14)

        block_items = parse_grocery_blocks(sparse_blocks)
        sparse_line_items = parse_grocery_lines(sparse_lines)
        dense_line_items = parse_grocery_lines(dense_lines)
        invoice_line_items = parse_grocery_lines(invoice_lines)

        candidates = [
            (block_items, sparse_lines),
            (sparse_line_items, sparse_lines),
            (dense_line_items, dense_lines),
            (invoice_line_items, invoice_lines),
        ]

        chosen_items, chosen_lines = max(candidates, key=lambda item: len(item[0]))

        return {
            "bill_type": bill_type,
            "items": _deduplicate_items(chosen_items),
            "lines": chosen_lines,
        }

    return {
        "bill_type": bill_type,
        "items": parse_restaurant_lines(dense_lines),
        "lines": dense_lines,
    }
