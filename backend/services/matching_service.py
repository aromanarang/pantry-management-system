import re

from rapidfuzz import fuzz, process

from backend.config import get_db


GENERIC_STOP_WORDS = {
    "fresh",
    "loose",
    "pack",
    "unit",
    "pcs",
    "pc",
    "restaurant",
    "hotel",
    "brand",
    "premium",
    "best",
    "quality",
}

GROCERY_ALIASES = {
    "desi tomato": "tomato",
    "cs desi tomato": "tomato",
    "paneer cubes": "paneer",
    "malai paneer": "paneer",
    "salted butter": "butter",
    "amul butter": "butter",
    "table butter": "butter",
    "refined oil": "oil",
    "cooking oil": "oil",
    "cooking oil sunflower": "oil",
    "soyabean oil": "oil",
    "soya oil": "oil",
    "mustard cooking oil": "mustard oil",
    "fresh onion": "onion",
    "onions": "onion",
    "potato new crop": "potato",
    "fresh tomato": "tomato",
    "tomatoes": "tomato",
    "ginger garlic": "ginger garlic paste",
    "ginger garlic masala": "ginger garlic paste",
    "green chilli": "green chilli",
    "green chillies": "green chilli",
    "red chilli powder": "chilli powder",
    "mirchi powder": "chilli powder",
    "haldi powder": "turmeric powder",
    "dhania powder": "coriander powder",
    "jeera powder": "cumin powder",
    "dhania seeds": "coriander seeds",
    "hara dhania": "fresh coriander",
    "coriander leaves": "fresh coriander",
    "dhania leaves": "fresh coriander",
    "cornflour": "corn flour",
    "maida": "all purpose flour",
    "atta maida": "all purpose flour",
    "wheat flour atta": "wheat flour",
    "kacha doodh": "milk",
    "milk toned": "milk",
    "dahi": "curd",
    "hari matar": "green peas",
    "matar": "green peas",
    "green capsicum": "capsicum",
    "baby potatoes": "baby potato",
    "aloo": "potato",
    "gobi": "cauliflower",
    "baingan": "eggplant",
    "bhindi": "okra",
    "rajma": "kidney beans",
    "chana": "chickpeas",
    "moong": "moong dal",
    "toor": "toor dal",
    "arhar dal": "toor dal",
    "ketchup": "tomato ketchup",
    "schezwan": "schezwan sauce",
}

MENU_ALIASES = {
    "panner butter masala": "paneer butter masala",
    "paneer butter masla": "paneer butter masala",
    "shahi panner": "shahi paneer",
    "kadai paneer": "kadhai paneer",
    "paneer do pyaja": "paneer do pyaza",
    "paneer bhurjee": "paneer bhurji",
    "aloo gobi masala": "aloo gobi",
    "veg curry": "mixed vegetable curry",
    "dal fry tadka": "dal fry",
    "punjabi chana masala": "punjabi chole",
    "veg manchuria": "veg manchurian",
    "hara bhara kebab": "hara bhara kabab",
    "gobi manchuria": "gobi manchurian",
    "veg seekh kebab": "veg seekh kebab",
    "paneer noodle": "paneer noodles",
    "veg noodle": "veg chowmein",
}


def normalize_text(text, aliases=None):
    normalized = text.lower().strip()
    normalized = re.sub(r"[\(\)\[\],:/\-]+", " ", normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", " ", normalized)
    normalized = re.sub(r"\b(rs|inr|mrp|qty|quantity|rate|price)\b", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    tokens = [token for token in normalized.split() if token not in GENERIC_STOP_WORDS]
    normalized = " ".join(tokens).strip()

    if aliases and normalized in aliases:
        normalized = aliases[normalized]

    return normalized


def _fetch_names(query):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(query)
    names = [row[0] for row in cursor.fetchall()]

    cursor.close()
    db.close()

    return names


def _match_name(extracted_name, choices, score_cutoff=60, aliases=None):
    if not extracted_name or not choices:
        return None

    normalized_choices = {
        normalize_text(choice, aliases=aliases): choice for choice in choices
    }
    extracted_normalized = normalize_text(extracted_name, aliases=aliases)

    if extracted_normalized in normalized_choices:
        return normalized_choices[extracted_normalized]

    result = process.extractOne(
        extracted_normalized,
        list(normalized_choices.keys()),
        scorer=fuzz.token_set_ratio,
        score_cutoff=score_cutoff,
    )

    if not result:
        return None

    matched_normalized = result[0]
    return normalized_choices[matched_normalized]


def match_ingredient(extracted_name, score_cutoff=60):
    ingredient_names = _fetch_names("SELECT ingredient_name FROM ingredients")
    return _match_name(
        extracted_name,
        ingredient_names,
        score_cutoff=score_cutoff,
        aliases=GROCERY_ALIASES,
    )


def match_menu_item(extracted_name, score_cutoff=60):
    menu_names = _fetch_names("SELECT menu_name FROM menu_items")
    return _match_name(
        extracted_name,
        menu_names,
        score_cutoff=score_cutoff,
        aliases=MENU_ALIASES,
    )
