"""Load recipes/<id>.yaml and prepare them for display. Shared by render_cards.py and build_site.py."""
import json
import pathlib
import re

import jsonschema
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "recipes"
MENUS_DIR = ROOT / "menus"
SCHEMA = json.loads((ROOT / "recipe.schema.json").read_text())
MENU_SCHEMA = json.loads((ROOT / "menu.schema.json").read_text())

# Cookbook order; the schema's enum lists categories in this order too.
CATEGORIES = {
    "beverages": "Beverages", "breads": "Breads", "cakes": "Cakes", "candy": "Candy",
    "canning-freezing": "Canning & Freezing", "breakfast": "Breakfast", "cookies": "Cookies",
    "condiments": "Condiments", "desserts": "Desserts", "main-dishes": "Main Dishes",
    "salads": "Salads", "snacks": "Snacks", "soups": "Soups", "vegetables": "Vegetables",
    "miscellaneous": "Miscellaneous",
}

FRACTIONS = {
    "1/2": "½", "1/3": "⅓", "2/3": "⅔", "1/4": "¼", "3/4": "¾",
    "1/8": "⅛", "3/8": "⅜", "5/8": "⅝", "7/8": "⅞", "1/6": "⅙", "5/6": "⅚",
}
# Units that read better pluralized ("2 cups"); abbreviations like tsp and oz stay as they are.
PLURAL_UNITS = {"cup", "pint", "can", "jar", "bag", "box", "stick", "bar", "clove", "slice",
                "pinch", "dash", "head", "bunch", "sprig", "piece"}
PLURAL_ABBREVIATED = {"lb": "lbs", "pkg": "pkgs"}


def _load_file(path: pathlib.Path, schema: dict) -> dict:
    doc = yaml.safe_load(path.read_text())
    try:
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as e:
        raise SystemExit(f"{path.relative_to(ROOT)}: {e.message} (at {'/'.join(map(str, e.absolute_path))})")
    if doc["id"] != path.stem:
        raise SystemExit(f"{path.relative_to(ROOT)}: id {doc['id']!r} doesn't match the file name")
    return doc


def load(directory: pathlib.Path = RECIPES_DIR) -> list[dict]:
    """Every recipe, validated, in cookbook order: by category, then title."""
    recipes = [_load_file(path, SCHEMA) for path in sorted(directory.glob("*.yaml"))]
    order = list(CATEGORIES)
    return sorted(recipes, key=lambda r: (order.index(r["category"]), r["title"].lower()))


def load_menus(recipe_ids: set[str], directory: pathlib.Path = MENUS_DIR) -> list[dict]:
    """Every menu, validated and checked against the recipes, newest first."""
    menus = []
    for path in sorted(directory.glob("*.yaml")):
        m = _load_file(path, MENU_SCHEMA)
        where = path.relative_to(ROOT)
        if m["id"] in recipe_ids:
            raise SystemExit(f"{where}: id {m['id']!r} is also a recipe id; the pages would collide")
        missing = [d for d in m["dishes"] if d not in recipe_ids]
        if missing:
            raise SystemExit(f"{where}: unknown recipe ids in dishes: {', '.join(missing)}")
        stray = [t["recipe"] for day in m.get("plan", []) for t in day["tasks"] if t.get("recipe") and t["recipe"] not in m["dishes"]]
        if stray:
            raise SystemExit(f"{where}: plan tasks name recipes that aren't in dishes: {', '.join(sorted(set(stray)))}")
        menus.append(m)
    return sorted(menus, key=lambda m: m["date"], reverse=True)


def pretty_fractions(text: str | None) -> str | None:
    """'1 1/2' -> '1½' anywhere in the text. Leaves "11/2", "1/24", and dates like "1/2/2020" alone."""
    if not text:
        return text
    for ascii_frac, glyph in FRACTIONS.items():
        text = re.sub(rf"(?:(\d) )?(?<![\d/]){re.escape(ascii_frac)}(?![\d/])", lambda m: (m.group(1) or "") + glyph, text)
    return text


def pretty_quantity(q: str | None) -> str:
    """'1 1/2' -> '1½', '2-3' -> '2–3'."""
    return pretty_fractions(q).replace("-", "–") if q else ""


def quantity_value(q: str | None) -> float | None:
    """Numeric value of a quantity's upper bound, for deciding singular vs plural units."""
    if not q:
        return None
    part = re.split(r"\s*(?:-|to)\s*", q)[-1]
    total = 0.0
    for token in part.split():
        if "/" in token:
            num, _, den = token.partition("/")
            if not (num.isdigit() and den.isdigit()) or den == "0":
                return None
            total += int(num) / int(den)
        else:
            try:
                total += float(token)
            except ValueError:
                return None
    return total


def pretty_unit(unit: str | None, q: str | None) -> str:
    if not unit:
        return ""
    value = quantity_value(q)
    if value is not None and value > 1:
        if unit in PLURAL_UNITS:
            return unit + "es" if unit.endswith(("sh", "ch")) else unit + "s"
        return PLURAL_ABBREVIATED.get(unit, unit)
    return unit


def ingredient_line(i: dict) -> dict:
    item = i["item"]
    if i.get("preparation"):
        item += f", {i['preparation']}"
    return {
        "amount": " ".join(filter(None, [pretty_quantity(i.get("quantity")), pretty_unit(i.get("unit"), i.get("quantity"))])),
        "item": item,
        "note": pretty_fractions(i.get("note")),
        "optional": i.get("optional", False),
    }


def first_name(author: str | None) -> str | None:
    return author.split()[0] if author else None


def display(r: dict) -> dict:
    """The recipe plus the formatted pieces templates need: byline, facts, ingredient lines."""
    facts = [
        ("Makes", r.get("yield")),
        ("Serves", r.get("servings")),
        ("Oven", f"{r['oven_temp_f']}°F" if r.get("oven_temp_f") else None),
        ("Prep", r.get("prep_time")),
        ("Cook", r.get("cook_time")),
        ("Wait", r.get("inactive_time")),
        ("Pan", r.get("pan")),
    ]
    byline = []
    if r.get("source"):
        byline.append(f"From {r['source']}")
    if r.get("author"):
        byline.append(f"{'Notes' if r.get('source') else 'Recipe'} by {first_name(r['author'])}")
    return {
        **r,
        "category_label": CATEGORIES[r["category"]],
        "byline": " · ".join(byline),
        "facts": [(k, v) for k, v in facts if v],
        "directions": [{"name": d["name"], "steps": [pretty_fractions(s) for s in d["steps"]]} for d in r["directions"]],
        "notes": [pretty_fractions(n) for n in r.get("notes", [])],
        "story": pretty_fractions(r.get("story")),
        "ingredient_groups": [
            {"name": g["name"], "ingredients": [ingredient_line(i) for i in g["ingredients"]]}
            for g in r["ingredient_groups"]
        ],
    }
