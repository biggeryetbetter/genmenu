"""Decorative images for menus: theme-coloured SVG clipart plus optional user-supplied pictures.

Images are never annotated; they are distractors that make layouts look more like real menus.
"""
import math
import random
from collections.abc import Callable
from pathlib import Path

from markupsafe import Markup

from .theme import ASSET_HOST

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


class ImageLibrary:
    """User-supplied pictures, served to the browser at {ASSET_HOST}/images/<index>."""

    def __init__(self, directory: Path | None):
        self.files: list[Path] = []
        if directory is not None and directory.is_dir():
            self.files = sorted(p for p in directory.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)

    def url(self, index: int) -> str:
        return f"{ASSET_HOST}/images/{index}{self.files[index].suffix.lower()}"

    def path_for(self, name: str) -> Path | None:
        stem = name.split(".")[0]
        if stem.isdigit() and int(stem) < len(self.files):
            return self.files[int(stem)]
        return None


# ---------------------------------------------------------------- SVG pieces
# Each takes (rng, palette) and returns SVG body markup for a 100x100 viewBox.
Palette = dict[str, str]
Piece = Callable[[random.Random, Palette], str]


def _steam(rng: random.Random, color: str, x0: float, y0: float) -> str:
    paths = []
    for i in range(rng.randrange(2, 4)):
        x = x0 + i * 10
        paths.append(f'<path d="M{x} {y0} q-6 -8 0 -16 t0 -16" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" opacity="0.7"/>')
    return "".join(paths)


def plate(rng: random.Random, c: Palette) -> str:
    food = rng.choice([c["primary"], c["accent"], c["secondary"]])
    garnish = "".join(
        f'<circle cx="{rng.uniform(35, 65):.1f}" cy="{rng.uniform(35, 65):.1f}" r="{rng.uniform(3, 6):.1f}" fill="{c["secondary"]}"/>'
        for _ in range(rng.randrange(2, 6))
    )
    return (f'<circle cx="50" cy="50" r="46" fill="{c["surface"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<circle cx="50" cy="50" r="34" fill="none" stroke="{c["border"]}" stroke-width="2"/>'
            f'<ellipse cx="50" cy="52" rx="{rng.uniform(16, 24):.1f}" ry="{rng.uniform(12, 18):.1f}" fill="{food}"/>' + garnish)


def bowl(rng: random.Random, c: Palette) -> str:
    return (_steam(rng, c["muted"], 38, 40) +
            f'<path d="M10 50 h80 a40 36 0 0 1 -80 0z" fill="{c["primary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<ellipse cx="50" cy="50" rx="40" ry="6" fill="{c["accent"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<rect x="38" y="84" width="24" height="6" rx="2" fill="{c["text"]}"/>')


def cup(rng: random.Random, c: Palette) -> str:
    return (_steam(rng, c["muted"], 32, 38) +
            f'<path d="M20 42 h52 v28 a20 20 0 0 1 -20 20 h-12 a20 20 0 0 1 -20 -20z" fill="{c["secondary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M72 50 a10 10 0 0 1 0 20" fill="none" stroke="{c["text"]}" stroke-width="4"/>'
            f'<ellipse cx="46" cy="92" rx="34" ry="4" fill="{c["border"]}"/>')


def leaf_sprig(rng: random.Random, c: Palette) -> str:
    leaves = []
    for i in range(rng.randrange(3, 6)):
        y = 80 - i * 14
        side = -1 if i % 2 else 1
        leaves.append(f'<ellipse cx="{50 + side * 12}" cy="{y}" rx="13" ry="6" fill="{c["secondary"]}" transform="rotate({side * -35} {50 + side * 12} {y})"/>')
    return f'<path d="M50 95 C48 70 52 40 50 10" fill="none" stroke="{c["text"]}" stroke-width="2"/>' + "".join(leaves)


def chili(rng: random.Random, c: Palette) -> str:
    return (f'<path d="M30 30 C40 70 60 90 88 92 C70 80 55 55 48 28z" fill="{c["primary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M30 30 q4 -10 16 -4 l2 2" fill="{c["secondary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M38 26 q-2 -12 8 -18" fill="none" stroke="{c["secondary"]}" stroke-width="4" stroke-linecap="round"/>')


def cutlery(rng: random.Random, c: Palette) -> str:
    ink = c["text"]
    return (f'<g fill="{ink}"><rect x="28" y="10" width="3" height="28"/><rect x="34" y="10" width="3" height="28"/>'
            f'<rect x="40" y="10" width="3" height="28"/><path d="M27 36 h17 v6 a8 8 0 0 1 -6 6 v42 h-5 v-42 a8 8 0 0 1 -6 -6z"/>'
            f'<path d="M62 10 c14 8 14 36 4 42 v38 h-5 v-80z"/></g>')


def burger(rng: random.Random, c: Palette) -> str:
    return (f'<path d="M14 46 a36 30 0 0 1 72 0z" fill="{c["accent"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M12 52 q8 -8 16 0 t16 0 t16 0 t16 0 t12 0" fill="none" stroke="{c["secondary"]}" stroke-width="6"/>'
            f'<rect x="14" y="56" width="72" height="12" rx="6" fill="{c["primary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M14 72 h72 v6 a8 8 0 0 1 -8 8 h-56 a8 8 0 0 1 -8 -8z" fill="{c["accent"]}" stroke="{c["text"]}" stroke-width="2"/>'
            + "".join(f'<ellipse cx="{x}" cy="{rng.uniform(26, 36):.1f}" rx="2" ry="1.2" fill="{c["surface"]}"/>' for x in range(30, 74, 9)))


def pizza(rng: random.Random, c: Palette) -> str:
    toppings = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{c["primary"]}"/>'
        for x, y in [(50, 34), (40, 52), (58, 56), (49, 72)][: rng.randrange(2, 5)]
    )
    return (f'<path d="M18 16 Q50 2 82 16 L50 94z" fill="{c["accent"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M18 16 Q50 2 82 16" fill="none" stroke="{c["secondary"]}" stroke-width="8" stroke-linecap="round"/>' + toppings)


def fish(rng: random.Random, c: Palette) -> str:
    return (f'<path d="M12 50 C30 22 66 22 78 50 C66 78 30 78 12 50z" fill="{c["secondary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<path d="M78 50 L94 34 L94 66z" fill="{c["primary"]}" stroke="{c["text"]}" stroke-width="2"/>'
            f'<circle cx="28" cy="46" r="3.5" fill="{c["text"]}"/>'
            f'<path d="M44 34 q8 16 0 32" fill="none" stroke="{c["text"]}" stroke-width="2"/>')


PIECES: list[Piece] = [plate, bowl, cup, leaf_sprig, chili, cutlery, burger, pizza, fish]


def _svg(body: str, view: str, cls: str, style: str = "") -> Markup:
    return Markup(f'<svg class="{cls}" viewBox="{view}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="{style}">{body}</svg>')


class Art:
    """Image factory used from templates. Seeded so normal and segmented renders get identical images."""

    def __init__(self, seed: int, palette: Palette, library: ImageLibrary):
        self.rng = random.Random(seed)
        self.c = palette
        self.library = library

    def _photo(self, cls: str) -> Markup:
        url = self.library.url(self.rng.randrange(len(self.library.files)))
        return Markup(f'<img class="{cls}" src="{url}" alt="">')

    def icon(self, cls: str = "art") -> Markup:
        """Small clipart only (never a photo)."""
        piece = self.rng.choice(PIECES)
        return _svg(piece(self.rng, self.c), "0 0 100 100", cls)

    def spot(self, cls: str = "art", photo_bias: float = 0.5) -> Markup:
        """A picture for a card or corner: a user image (if any) with probability `photo_bias`, else clipart."""
        if self.library.files and self.rng.random() < photo_bias:
            return self._photo(cls)
        piece = self.rng.choice(PIECES)
        return _svg(f'<rect width="100" height="100" fill="{self.c["surface"]}"/>' + piece(self.rng, self.c),
                    "0 0 100 100", cls, "background: var(--surface);")

    def banner(self, cls: str = "banner-art") -> Markup:
        """A wide header picture: a user image or a scattered clipart pattern."""
        if self.library.files and self.rng.random() < 0.6:
            return self._photo(cls)
        tiles = []
        for _ in range(self.rng.randrange(8, 16)):
            piece = self.rng.choice(PIECES)
            x, y = self.rng.uniform(-20, 580), self.rng.uniform(-20, 140)
            size = self.rng.uniform(40, 90)
            rot = self.rng.uniform(-30, 30)
            tiles.append(f'<svg x="{x:.0f}" y="{y:.0f}" width="{size:.0f}" height="{size:.0f}" viewBox="0 0 100 100" opacity="0.55">'
                         f'<g transform="rotate({rot:.0f} 50 50)">{piece(self.rng, self.c)}</g></svg>')
        body = f'<rect width="600" height="200" fill="{self.c["primary"]}"/>' + "".join(tiles)
        return Markup(f'<svg class="{cls}" viewBox="0 0 600 200" preserveAspectRatio="xMidYMid slice"'
                      f' xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{body}</svg>')

    def divider(self, cls: str = "divider") -> Markup:
        """A horizontal flourish."""
        ink = self.rng.choice([self.c["accent"], self.c["muted"], self.c["primary"]])
        style = self.rng.randrange(3)
        if style == 0:
            body = (f'<path d="M10 20 H130 M170 20 H290" stroke="{ink}" stroke-width="1.5"/>'
                    f'<path d="M150 10 L160 20 L150 30 L140 20z" fill="{ink}"/>'
                    f'<circle cx="132" cy="20" r="2.5" fill="{ink}"/><circle cx="168" cy="20" r="2.5" fill="{ink}"/>')
        elif style == 1:
            body = (f'<path d="M20 20 C60 20 80 6 110 14 C130 20 140 30 150 20 C160 10 170 20 190 26 C220 34 240 20 280 20"'
                    f' fill="none" stroke="{ink}" stroke-width="2"/>')
        else:
            body = "".join(f'<circle cx="{x}" cy="20" r="{3 if x == 150 else 1.8}" fill="{ink}"/>' for x in range(30, 280, 15))
        return _svg(body, "0 0 300 40", cls)

    def badge(self, text: str, cls: str = "badge-art") -> Markup:
        """A starburst sticker with a short word on it."""
        points = []
        n = 14
        for i in range(n * 2):
            r = 48 if i % 2 == 0 else 38
            a = math.pi * i / n
            points.append(f"{50 + r * math.cos(a):.1f},{50 + r * math.sin(a):.1f}")
        fill = self.rng.choice([self.c["accent"], self.c["primary"]])
        return _svg(f'<polygon points="{" ".join(points)}" fill="{fill}"/>'
                    f'<text x="50" y="56" text-anchor="middle" font-size="18" font-weight="700" fill="{self.c["on-primary"]}"'
                    f' font-family="sans-serif">{text}</text>', "0 0 100 100", cls)
