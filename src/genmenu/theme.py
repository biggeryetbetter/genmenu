"""Random colour palettes (with contrast guarantees) and bundled font selection."""
import colorsys
import random
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
ASSET_HOST = "https://genmenu.local"


# ---------------------------------------------------------------- colours

def hsl(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, min(1.0, max(0.0, l)), min(1.0, max(0.0, s)))
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def luminance(color: str) -> float:
    def channel(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def fit(h: float, s: float, l: float, against: list[str], ratio: float, step: float) -> str:
    """Move lightness by `step` until the colour reaches `ratio` contrast with every colour in `against`."""
    color = hsl(h, s, l)
    for _ in range(100):
        if all(contrast(color, a) >= ratio for a in against):
            break
        l = min(1.0, max(0.0, l + step))
        color = hsl(h, s, l)
    return color


# Hue offsets for primary / secondary / accent
SCHEMES: dict[str, tuple[float, float, float]] = {
    "monochrome": (0.0, 0.0, 0.0),
    "analogous": (0.0, 1 / 12, -1 / 12),
    "complementary": (0.0, 0.5, 0.0),
    "split-complementary": (0.0, 5 / 12, 7 / 12),
    "triadic": (0.0, 1 / 3, 2 / 3),
}


def random_palette(mode: str) -> tuple[str, dict[str, str]]:
    scheme = random.choice(list(SCHEMES))
    h = random.random()
    bg_s = random.uniform(0.05, 0.5)
    dark = mode == "dark"
    if dark:
        bg_l = random.uniform(0.06, 0.18)
        surface_l = bg_l + random.choice([0.0, random.uniform(0.03, 0.09)])
        text_l, step = random.uniform(0.86, 0.97), 0.02
    else:
        bg_l = random.uniform(0.9, 0.99)
        surface_l = random.choice([1.0, bg_l - random.uniform(0.0, 0.06), min(1.0, bg_l + 0.04)])
        text_l, step = random.uniform(0.08, 0.24), -0.02
    bg = hsl(h, bg_s, bg_l)
    surface = hsl(h, bg_s, surface_l)
    grounds = [bg, surface]
    text = fit(h, random.uniform(0.0, 0.3), text_l, grounds, 7.0, step)
    muted = fit(h, random.uniform(0.0, 0.25), (bg_l + text_l) / 2, grounds, 4.5, step)
    accent_l = 0.62 if dark else 0.42
    p_off, s_off, a_off = SCHEMES[scheme]
    primary = fit(h + p_off, random.uniform(0.45, 0.9), accent_l, grounds, 4.5, step)
    secondary = fit(h + s_off, random.uniform(0.35, 0.85), accent_l + random.uniform(-0.1, 0.1), grounds, 4.5, step)
    accent = fit(h + a_off + (random.uniform(-0.04, 0.04) if scheme == "monochrome" else 0.0),
                 random.uniform(0.5, 0.95), accent_l, grounds, 4.5, step)
    border = hsl(h, bg_s, bg_l + (text_l - bg_l) * 0.25)
    on_primary = max(["#ffffff", "#111111"], key=lambda c: contrast(c, primary))
    return scheme, {
        "bg": bg, "surface": surface, "text": text, "muted": muted, "border": border,
        "primary": primary, "secondary": secondary, "accent": accent, "on-primary": on_primary,
    }


# ---------------------------------------------------------------- fonts

@dataclass(frozen=True)
class FontFile:
    path: str           # relative to FONT_DIR
    style: str = "normal"
    weight: str = "100 900"


@dataclass(frozen=True)
class Font:
    key: str
    family: str
    generic: str
    files: tuple[FontFile, ...]
    body_ok: bool = True    # script/display faces are only used for headings

    @property
    def stack(self) -> str:
        return f"'{self.family}', {self.generic}"


FONTS: list[Font] = [
    Font("roboto", "Roboto", "sans-serif", (FontFile("roboto/Roboto[wdth,wght].ttf"), FontFile("roboto/Roboto-Italic[wdth,wght].ttf", "italic"))),
    Font("opensans", "Open Sans", "sans-serif", (FontFile("opensans/OpenSans[wdth,wght].ttf"), FontFile("opensans/OpenSans-Italic[wdth,wght].ttf", "italic"))),
    Font("oswald", "Oswald", "sans-serif", (FontFile("oswald/Oswald[wght].ttf", weight="200 700"),)),
    Font("lora", "Lora", "serif", (FontFile("lora/Lora[wght].ttf", weight="400 700"), FontFile("lora/Lora-Italic[wght].ttf", "italic", "400 700"))),
    Font("playfair", "Playfair Display", "serif", (FontFile("playfairdisplay/PlayfairDisplay[wght].ttf", weight="400 900"), FontFile("playfairdisplay/PlayfairDisplay-Italic[wght].ttf", "italic", "400 900"))),
    Font("robotoslab", "Roboto Slab", "serif", (FontFile("robotoslab/RobotoSlab[wght].ttf"),)),
    Font("courierprime", "Courier Prime", "monospace", (FontFile("courierprime/CourierPrime-Regular.ttf", weight="400"), FontFile("courierprime/CourierPrime-Italic.ttf", "italic", "400"), FontFile("courierprime/CourierPrime-Bold.ttf", weight="700"))),
    Font("pacifico", "Pacifico", "cursive", (FontFile("pacifico/Pacifico-Regular.ttf", weight="400"),), body_ok=False),
    Font("lobster", "Lobster", "cursive", (FontFile("lobster/Lobster-Regular.ttf", weight="400"),), body_ok=False),
    Font("bebasneue", "Bebas Neue", "sans-serif", (FontFile("bebasneue/BebasNeue-Regular.ttf", weight="400"),), body_ok=False),
]
FONTS_BY_KEY = {f.key: f for f in FONTS}


def font_face_css(fonts: list[Font]) -> str:
    rules = []
    for font in fonts:
        for f in font.files:
            rules.append(
                f"@font-face {{ font-family: '{font.family}'; font-style: {f.style}; font-weight: {f.weight};"
                f" src: url('{ASSET_HOST}/fonts/{quote(f.path)}') format('truetype'); }}"
            )
    return "\n".join(rules)


# ---------------------------------------------------------------- theme

@dataclass
class Theme:
    mode: str
    scheme: str
    colors: dict[str, str]
    heading_font: Font
    body_font: Font
    base_size: int

    def css(self) -> str:
        """@font-face rules plus a :root block of CSS custom properties."""
        fonts = [self.heading_font] if self.heading_font == self.body_font else [self.heading_font, self.body_font]
        props = [f"--{k}: {v};" for k, v in self.colors.items()]
        props += [
            f"--font-heading: {self.heading_font.stack};",
            f"--font-body: {self.body_font.stack};",
            f"--base-size: {self.base_size}px;",
        ]
        return font_face_css(fonts) + "\n:root { " + " ".join(props) + " }"

    def describe(self) -> dict[str, str]:
        return {"mode": self.mode, "scheme": self.scheme,
                "heading_font": self.heading_font.key, "body_font": self.body_font.key}


def random_theme(mode: str | None = None, heading_fonts: list[str] | None = None) -> Theme:
    mode = mode or random.choice(["light", "dark"])
    scheme, colors = random_palette(mode)
    heading_pool = [FONTS_BY_KEY[k] for k in heading_fonts] if heading_fonts else FONTS
    heading = random.choice(heading_pool)
    body = heading if heading.body_ok and random.random() < 0.3 else random.choice([f for f in FONTS if f.body_ok])
    return Theme(mode, scheme, colors, heading, body, random.randrange(13, 19))
