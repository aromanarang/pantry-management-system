from backend.config import get_db


MASS_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
}

VOLUME_TO_LITRE = {
    "litre": 1.0,
    "liter": 1.0,
    "l": 1.0,
    "ml": 0.001,
}

COUNT_UNITS = {
    "unit",
    "units",
    "pc",
    "pcs",
    "piece",
    "pieces",
    "pack",
    "packet",
    "packets",
}

# Approximate ingredient densities in kg per litre.
DENSITY_KG_PER_LITRE = {
    "oil": 0.92,
    "mustard oil": 0.92,
    "cream": 1.01,
    "curd": 1.03,
    "lemon juice": 1.03,
    "soy sauce": 1.16,
    "vinegar": 1.01,
    "red chilli sauce": 1.18,
    "tomato ketchup": 1.30,
    "milk": 1.03,
    "schezwan sauce": 1.15,
    "ghee": 0.91,
}


def normalize_unit(unit):
    if unit is None:
        return None

    normalized = unit.strip().lower()

    aliases = {
        "kgs": "kg",
        "gram": "g",
        "grams": "g",
        "ltr": "litre",
        "litres": "litre",
        "liters": "litre",
        "millilitre": "ml",
        "millilitres": "ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "pieces": "pcs",
    }

    return aliases.get(normalized, normalized)


def get_ingredient_details(ingredient_name):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT ingredient_id, ingredient_name, unit FROM ingredients WHERE ingredient_name=%s",
        (ingredient_name,),
    )
    ingredient = cursor.fetchone()

    cursor.close()
    db.close()

    return ingredient


def _convert_mass(quantity, source_unit, target_unit):
    quantity_in_kg = quantity * MASS_TO_KG[source_unit]

    if target_unit == "kg":
        return quantity_in_kg

    return quantity_in_kg / MASS_TO_KG[target_unit]


def _convert_volume(quantity, source_unit, target_unit):
    quantity_in_litre = quantity * VOLUME_TO_LITRE[source_unit]

    if target_unit == "litre":
        return quantity_in_litre

    return quantity_in_litre / VOLUME_TO_LITRE[target_unit]


def _density_for(ingredient_name):
    return DENSITY_KG_PER_LITRE.get(ingredient_name.lower())


def convert_quantity_for_ingredient(ingredient_name, quantity, source_unit, target_unit):
    source_unit = normalize_unit(source_unit)
    target_unit = normalize_unit(target_unit)
    quantity = float(quantity)

    if source_unit is None or target_unit is None:
        raise ValueError("Both source unit and target unit are required")

    if source_unit == target_unit:
        return quantity

    if source_unit in MASS_TO_KG and target_unit in MASS_TO_KG:
        return _convert_mass(quantity, source_unit, target_unit)

    if source_unit in VOLUME_TO_LITRE and target_unit in VOLUME_TO_LITRE:
        return _convert_volume(quantity, source_unit, target_unit)

    density = _density_for(ingredient_name)

    if density is None:
        raise ValueError(
            f"No ingredient-specific conversion configured for {ingredient_name} from {source_unit} to {target_unit}"
        )

    if source_unit in VOLUME_TO_LITRE and target_unit in MASS_TO_KG:
        quantity_in_litre = quantity * VOLUME_TO_LITRE[source_unit]
        quantity_in_kg = quantity_in_litre * density
        return quantity_in_kg / MASS_TO_KG[target_unit]

    if source_unit in MASS_TO_KG and target_unit in VOLUME_TO_LITRE:
        quantity_in_kg = quantity * MASS_TO_KG[source_unit]
        quantity_in_litre = quantity_in_kg / density
        return quantity_in_litre / VOLUME_TO_LITRE[target_unit]

    if source_unit in COUNT_UNITS or target_unit in COUNT_UNITS:
        raise ValueError(f"Cannot automatically convert {source_unit} to {target_unit} for {ingredient_name}")

    raise ValueError(f"Unsupported unit conversion from {source_unit} to {target_unit}")


def normalize_quantity_to_db_unit(ingredient_name, quantity, source_unit=None):
    ingredient = get_ingredient_details(ingredient_name)

    if not ingredient:
        raise ValueError(f"Ingredient not found: {ingredient_name}")

    target_unit = normalize_unit(ingredient["unit"])
    source_unit = normalize_unit(source_unit) or target_unit
    converted_quantity = convert_quantity_for_ingredient(
        ingredient_name=ingredient["ingredient_name"],
        quantity=quantity,
        source_unit=source_unit,
        target_unit=target_unit,
    )

    return {
        "ingredient_id": ingredient["ingredient_id"],
        "ingredient_name": ingredient["ingredient_name"],
        "source_unit": source_unit,
        "target_unit": target_unit,
        "converted_quantity": converted_quantity,
    }
