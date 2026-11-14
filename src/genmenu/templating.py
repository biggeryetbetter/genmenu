"""Layouts, random render settings and HTML rendering."""
import mimetypes
import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup
from playwright.sync_api import Page, Route

from .annotations import segmented_css
from .clipart import Art, ImageLibrary
from .menu_data import random_menu, menu_to_structured
from .theme import ASSET_HOST, FONT_DIR, Theme, random_theme

env = Environment(
    loader=PackageLoader("genmenu"),
    autoescape=select_autoescape(["html", "jinja"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
# badges short enough to fit on a starburst sticker
# pyrefly: ignore[bad-argument-type, unsupported-operation]
env.tests["short"] = lambda s: len(s) <= 5


@dataclass(frozen=True)
class Layout:
    name: str
    template: str
    modes: tuple[str, ...] = ("light", "dark")
    sections: bool = False      # renders menu["sections"] with headings
    grid: bool = False          # every section is a size grid
    min_width: int = 480        # smallest sensible viewport width


LAYOUTS: list[Layout] = [
    Layout("cards", "menu-layout-1.html.jinja"),
    Layout("classic-list", "menu-layout-2.html.jinja"),
    Layout("chalkboard", "menu-layout-3.html.jinja", modes=("dark",)),
    Layout("two-column", "menu-layout-4.html.jinja", sections=True),
    Layout("size-grid", "menu-layout-5.html.jinja", sections=True, grid=True),
    Layout("photo-cards", "menu-layout-6.html.jinja", sections=True),
    Layout("price-first", "menu-layout-7.html.jinja", sections=True),
    Layout("poster", "menu-layout-8.html.jinja", sections=True, min_width=600),
    Layout("fine-dining", "menu-layout-9.html.jinja", sections=True),
]
LAYOUTS_BY_NAME = {layout.name: layout for layout in LAYOUTS}


def _num(p: float, decimals: str = ".") -> str:
    return f"{p:.2f}".replace(".", decimals)


# name -> formatter; one is chosen per menu
PRICE_FORMATS: dict[str, Callable[[float], str]] = {
    "dollar-cents": lambda p: f"${p:.2f}",
    "dollar-short": lambda p: f"${p:.0f}" if p.is_integer() else f"${p:.2f}",
    "plain-cents": lambda p: f"{p:.2f}",
    "plain-short": lambda p: f"{p:g}",
    "integer": lambda p: f"{round(p)}",
    "euro-prefix": lambda p: f"€{_num(p, ',')}",
    "euro-suffix": lambda p: f"{_num(p, ',')} €",
    "pound": lambda p: f"£{p:.2f}",
    "swiss-dash": lambda p: f"{p:.0f}.–" if p.is_integer() else f"{p:.2f}",
}


@dataclass
class Sample:
    """Everything needed to render one image deterministically (normal and segmented)."""
    layout: Layout
    menu: dict[str, Any]
    theme: Theme
    price_format: str
    art_seed: int
    width: int

    def describe(self) -> dict[str, Any]:
        return {"layout": self.layout.name, "price_format": self.price_format, "structured": menu_to_structured(self.menu), **self.theme.describe()}


def random_sample(min_width: int, max_width: int, layout: str | None = None) -> Sample:
    lay = LAYOUTS_BY_NAME[layout] if layout else random.choice(LAYOUTS)
    return Sample(
        layout=lay,
        menu=random_menu(grid=lay.grid, sections=lay.sections),
        theme=random_theme(random.choice(lay.modes)),
        price_format=random.choice(list(PRICE_FORMATS)),
        art_seed=random.randrange(2 ** 31),
        width=random.randrange(max(min_width, lay.min_width), max(max_width, lay.min_width) + 1),
    )


def render(sample: Sample, library: ImageLibrary, segmented: bool = False) -> str:
    template = env.get_template(sample.layout.template)
    return template.render(
        sample.menu,
        theme_css=Markup(sample.theme.css()),
        segmented=segmented,
        segmented_css=Markup(segmented_css()) if segmented else "",
        price=PRICE_FORMATS[sample.price_format],
        art=Art(sample.art_seed, sample.theme.colors, library),
    )


def install_asset_routes(page: Page, library: ImageLibrary) -> None:
    """Serve bundled fonts and user images to pages loaded with set_content()."""
    cache: dict[Path, bytes] = {}

    def handle(route: Route) -> None:
        path = unquote(urlparse(route.request.url).path)
        file: Path | None = None
        if path.startswith("/fonts/"):
            candidate = (FONT_DIR / path.removeprefix("/fonts/")).resolve()
            if candidate.is_relative_to(FONT_DIR.resolve()) and candidate.is_file():
                file = candidate
        elif path.startswith("/images/"):
            file = library.path_for(path.removeprefix("/images/"))
        if file is None:
            route.fulfill(status=404)
            return
        if file not in cache:
            cache[file] = file.read_bytes()
        content_type = mimetypes.guess_type(file.name)[0] or ("font/ttf" if file.suffix == ".ttf" else "application/octet-stream")
        route.fulfill(status=200, body=cache[file], headers={"Content-Type": content_type, "Access-Control-Allow-Origin": "*"})

    page.route(f"{ASSET_HOST}/**", handle)
