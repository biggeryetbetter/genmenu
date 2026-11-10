"""Annotation categories, bounding-box extraction and debug visualisations."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Page
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class Category:
    name: str
    selector: str
    # Containers hold other annotated elements; in the segmented debug view they are drawn
    # as outlined tinted regions instead of solid fills.
    container: bool = False


# Index in this list == COCO category id. Only append, so ids stay stable across dataset versions.
CATEGORIES: list[Category] = [
    Category("title", ".ann-title"),
    Category("subtitle", ".ann-subtitle"),
    Category("menu_item", ".ann-item", container=True),
    Category("item_title", ".ann-item-title"),
    Category("item_description", ".ann-item-desc"),
    Category("variant", ".ann-variant", container=True),
    Category("variant_title", ".ann-variant-title"),
    Category("variant_price", ".ann-variant-price"),
    Category("item_price", ".ann-item-price"),
    Category("section_title", ".ann-section-title"),
]
ID2LABEL = {i: c.name for i, c in enumerate(CATEGORIES)}

# Debug colour per category (overlay boxes and segmented render)
COLORS = [
    (230, 25, 75), (60, 180, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180),
    (70, 240, 240), (240, 50, 230), (128, 128, 0), (0, 128, 128), (255, 215, 0),
]


def segmented_css() -> str:
    """CSS that paints every annotated element in its category colour (debug mode)."""
    rules = ["img, svg { opacity: 0.25 !important; }"]
    for i, cat in enumerate(CATEGORIES):
        r, g, b = COLORS[i % len(COLORS)]
        if cat.container:
            rules.append(
                f"{cat.selector} {{ outline: 2px dashed rgb({r},{g},{b}) !important; outline-offset: -1px;"
                f" background-color: rgba({r},{g},{b},0.18) !important; color: transparent !important; }}"
            )
        else:
            rules.append(
                f"{cat.selector} {{ background-color: rgb({r},{g},{b}) !important;"
                f" color: transparent !important; text-shadow: none !important; }}"
            )
    return "\n".join(rules)


def extract_annotations(page: Page, width: int, height: int) -> list[dict[str, Any]]:
    """Return COCO-style annotations (bbox = [x, y, w, h] in image pixels) for every annotated element."""
    scroll_x, scroll_y = page.evaluate("[window.scrollX, window.scrollY]")
    anns: list[dict[str, Any]] = []
    for category_id, cat in enumerate(CATEGORIES):
        for el in page.locator(cat.selector).all():
            bbox = el.bounding_box()
            if bbox is None:
                continue
            x0 = max(0.0, bbox["x"] + scroll_x)
            y0 = max(0.0, bbox["y"] + scroll_y)
            x1 = min(float(width), bbox["x"] + scroll_x + bbox["width"])
            y1 = min(float(height), bbox["y"] + scroll_y + bbox["height"])
            w, h = x1 - x0, y1 - y0
            if w < 1 or h < 1:
                continue
            anns.append({"category_id": category_id, "bbox": [round(x0, 2), round(y0, 2), round(w, 2), round(h, 2)]})
    return anns


def draw_annotations(image_path: Path, anns: list[dict[str, Any]], out_path: Path) -> None:
    """Save a copy of the image with class-coloured boxes and labels drawn over it."""
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    for ann in anns:
        x, y, w, h = ann["bbox"]
        color = COLORS[ann["category_id"] % len(COLORS)]
        draw.rectangle((x, y, x + w, y + h), fill=(*color, 40), outline=(*color, 255), width=2)
        draw.text((x + 2, y + 1), ID2LABEL[ann["category_id"]], fill=(*color, 255))
    img.alpha_composite(overlay)
    img.convert("RGB").save(out_path)
