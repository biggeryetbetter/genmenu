"""Random menu content: titles, sections, items, variants, badges and footer details."""
import jsonschema
import json
import random
from random import choice, randrange
from typing import Any

item_types = ["sandwich", "burger", "wrap", "taco", "tapa", "pepper", "fish dish", "hot dish", "soup", "stew", "phō"]
adjectives = ["beef", "soupy", "pork", "chicken", "turkey", "mutton", "lamb", "fishy", "hot", "drip", "gagging", "dirt", "shat", "crass"]
verbs = ["cooked", "brothed", "beequeethed", "eaten", "made", "smashed", "worn", "grilled", "fried", "boiled", "shot", "shat"]
adverbs = ["beefily", "soupily", "porkly", "chickenly", "turkely", "muttonly", "lambly", "fishily", "hotly", "drippingly", "gaggingly", "dirtily", "crassly"]

place_owners = ["Borg", "Mama Rosa's", "Uncle Bo's", "The Golden", "Big Jim's", "Le Petit", "Lucky", "Old Town", "Señor", "Captain's",
                "Blue Door", "Little Lamb", "The Rusty", "Chez Marcel", "Nonna's", "Red Lantern", "Hungry Fox"]
place_nouns = ["Cáfe", "Diner", "Bistro", "Grill", "Kitchen", "Eatery", "Cantina", "Tavern", "Noodle Bar", "Smokehouse",
               "Trattoria", "Brasserie", "Pizzeria", "Taqueria", "Canteen", "Coffee House"]
taglines = [
    "Eat your shorts.", "Food, probably.", "Since yesterday.", "Hot and ready.", "You'll be back.",
    "Family owned, family eaten.", "No refunds.", "Tastes like {adj}.", "{adv} {verb} since 1987.",
    "Home of the {adj} {item}.", "Est. {year}", "Fresh · Local · {Adj}", "Open late, closed early.",
    "Where every {item} is {adj}.",
]

section_names = ["Starters", "Appetizers", "Small Plates", "Mains", "Soups", "Salads", "Sandwiches", "Burgers", "Pizza",
                 "Pasta", "Sides", "Desserts", "Drinks", "Coffee & Tea", "Specials", "From the Grill", "Kids", "Brunch",
                 "Bowls", "Tacos", "Chef's Selection", "Cocktails", "Wines"]
# Shared size sets for size-grid sections (also used as option names elsewhere)
size_sets = [
    ["Small", "Medium", "Large"], ["S", "M", "L"], ["Regular", "Large"], ["Cup", "Bowl"], ["Glass", "Bottle"],
    ["Half", "Full"], ['6"', '12"'], ["Single", "Double"], ['10"', '14"', '18"'], ["Small", "Large"],
    ["Tall", "Grande", "Venti"], ["1 pc", "3 pc", "6 pc"],
]
option_names = ["with fries", "with salad", "with rice", "Combo", "Spicy", "Vegetarian", "Extra cheese", "Family size",
                "Lunch portion", "Gluten free"]
badges = ["NEW", "V", "VG", "GF", "Spicy", "Chef's pick", "Popular", "🌶", "★", "Seasonal", "House favourite"]

streets = ["Main", "Oak", "Elm", "Harbor", "Mill", "Church", "Market", "Station", "Bridge", "Maple"]
street_suffixes = ["St", "Street", "Ave", "Road", "Blvd", "Lane"]
cities = ["Springfield", "Riverton", "Lakeside", "Fairview", "Kingsport", "Ashford", "Brookhaven"]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def random_title() -> str:
    return f"{choice(place_owners)} {choice(place_nouns)}"


def random_subtitle() -> str:
    adj = choice(adjectives)
    return choice(taglines).format(adj=adj, Adj=adj.capitalize(), adv=choice(adverbs).capitalize(),
                                   verb=choice(verbs), item=choice(item_types), year=randrange(1952, 2024))


def random_dish_name() -> str:
    what_is_it = choice(item_types)
    kind = randrange(0, 4)
    if kind == 0:
        name = f"{choice(adverbs)} {choice(verbs)} {choice(adjectives)} {what_is_it}"
    elif kind == 1:
        name = f"{choice(verbs)} {choice(adjectives)} {choice(item_types)} {what_is_it}"
    elif kind == 2:
        name = f"{choice(adjectives)} {choice(item_types)} {what_is_it}"
    else:
        name = f"{choice(verbs)} {choice(item_types)} {what_is_it}"
    return name.title() if random.random() < 0.3 else name


def random_description(name: str) -> str:
    what_is_it = name.split()[-1].lower()
    kind = randrange(0, 3)
    if kind == 0:
        return f"{choice(adverbs).capitalize()} {choice(verbs)} {what_is_it}. It's {choice(adjectives)}, {choice(adjectives)}, {choice(adjectives)}, and most importantly, {choice(adjectives)}."
    if kind == 1:
        return f"{choice(adjectives).capitalize()}, {choice(adjectives)} and {choice(verbs)}."
    return f"Served with {choice(adjectives)} {choice(item_types)} and a {choice(adjectives)} {choice(item_types)}."


def random_price(low: float = 3, high: float = 60) -> float:
    whole = randrange(int(low), int(high))
    return whole + choice([0.0, 0.0, 0.0, 0.5, 0.95, 0.99, 0.25, 0.75])


def random_item(sizes: list[str] | None = None) -> dict[str, Any]:
    """One menu item. With `sizes`, the item gets one variant per size (some sizes may be missing)."""
    name = random_dish_name()
    item: dict[str, Any] = {
        "name": name,
        "desc": random_description(name) if random.random() < 0.85 else "",
        "badges": random.sample(badges, k=choice([0, 0, 0, 1, 1, 2])),
    }
    if sizes is not None:
        base = random_price(3, 30)
        item["variants"] = [
            {"name": size, "_kind": 0, "price": round(base + i * choice([1, 2, 2.5, 3, 4]), 2)}
            if i == 0 or random.random() < 0.9 else None
            for i, size in enumerate(sizes)
        ]
        return item
    if random.random() < 0.4:
        kind = randrange(0, 3)
        n = randrange(2, 6)
        if kind == 0:
            names = choice(size_sets)
        elif kind == 1:
            names = random.sample(option_names, k=min(n, 4))
        else:
            names = [random_dish_name() for _ in range(n)]
        base = random_price()
        item["variants"] = [{"name": v, "_kind": kind, "price": round(base + i * choice([0.5, 1, 2, 3]), 2)} for i, v in enumerate(names)]
    else:
        item["price"] = random_price()
    return item


def random_section(name: str, grid: bool) -> dict[str, Any]:
    sizes = choice(size_sets) if grid else None
    return {
        "name": name,
        "sizes": sizes,
        "dishes": [random_item(sizes) for _ in range(randrange(2, 7))],  # not "items": clashes with dict.items in Jinja
    }


def random_footer() -> dict[str, str]:
    open_day, close_day = sorted(random.sample(range(7), 2))
    return {
        "address": f"{randrange(1, 999)} {choice(streets)} {choice(street_suffixes)}, {choice(cities)}",
        "hours": f"{days[open_day]}–{days[close_day]} {randrange(7, 12)}am–{randrange(8, 12)}pm",
        "phone": f"(555) {randrange(100, 999)}-{randrange(1000, 9999)}",
    }


def random_menu(grid: bool = False, sections: bool = False) -> dict[str, Any]:
    """Build a menu.

    `items` is always the flat list of all items (for layouts without sections).
    `grid=True` makes every section a size grid; otherwise some sections may be grids anyway.
    """
    n_sections = randrange(2, 5) if sections or grid else 1
    names = random.sample(section_names, k=n_sections)
    secs = [random_section(n, grid or random.random() < 0.15) for n in names]
    if not (sections or grid):
        # Flat layouts: a single unnamed section with more items
        secs[0]["dishes"] += [random_item() for _ in range(randrange(1, 7))]
    # Grid items may have None gaps in `variants`; list-style templates iterate `item.variants|select`.
    items = [it for s in secs for it in s["dishes"]]
    return {
        "title": random_title(),
        "subtitle": random_subtitle(),
        "sections": secs,
        "items": items,
        "footer": random_footer(),
        "show_footer": random.random() < 0.5,
    }

with open("schema.json", 'r') as s:
    schema = json.load(s)

def menu_to_structured(menu: dict[str, Any]) -> dict[str, Any]:
    sections = [
        { 
            "name": i["name"],
            "items": [
                {
                    "name": d["name"],
                    "desc": d["desc"],
                    "price": d["price"],
                } for d in i["dishes"] if not "variants" in d.keys()
            ],
            "varying_items": [ 
                {
                    "name": d["name"],
                    "desc": d["desc"],
                    "variants": [{
                        "name": var["name"],
                        "type": ["size", None, "subdish"][var["_kind"]],
                        "price": var["price"]
                    } for var in d["variants"] if var != None if var["_kind"] != 1 ],
                    "addons": [{
                        "name": add["name"],
                        "type": ["size", "addon", "subdish"][add["_kind"]],
                        "price": add["price"]
                    } for add in d["variants"] if add != None if add["_kind"] == 1 ]
                } for d in i["dishes"] if "variants" in d.keys()
            ],
        } for i in menu["sections"]
    ]
    out = {
        "title": menu["title"],
        "subtitle": menu["subtitle"],
        "sections": sections,
    }

    try:
        jsonschema.validate(out, schema)
    except jsonschema.ValidationError as e:
        print("WARNING: menu was not valid!\n", e)

    return out