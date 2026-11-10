"""genmenu: generate a synthetic menu object-detection dataset (Hugging Face imagefolder format)."""
import argparse
import json
import random
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright
from PIL import Image

from .annotations import ID2LABEL, draw_annotations, extract_annotations
from .clipart import ImageLibrary
from .templating import LAYOUTS_BY_NAME, install_asset_routes, random_sample, render


def load(page: Page, html: str) -> None:
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic menu object-detection dataset (HF imagefolder format).")
    parser.add_argument("--count", type=int, default=500, help="number of images to generate")
    parser.add_argument("--val-fraction", type=float, default=0.2, help="fraction of images in the validation split")
    parser.add_argument("--out", type=Path, default=Path("out/dataset"), help="output directory")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument("--min-width", type=int, default=480, help="minimum viewport width")
    parser.add_argument("--max-width", type=int, default=1400, help="maximum viewport width")
    parser.add_argument("--layout", choices=sorted(LAYOUTS_BY_NAME), default=None, help="only use this layout")
    parser.add_argument("--images", type=Path, default=Path("assets/images"),
                        help="folder of extra pictures for image layouts (used if it exists)")
    parser.add_argument("--debug", action="store_true",
                        help="also write HTML, CSS-segmented renders and PIL box overlays to <out>/debug")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    library = ImageLibrary(args.images)
    if library.files:
        print(f"Using {len(library.files)} images from {args.images}")

    out: Path = args.out
    n_val = round(args.count * args.val_fraction)
    splits = {"train": args.count - n_val, "validation": n_val}
    for split in splits:
        (out / split).mkdir(parents=True, exist_ok=True)
    debug_dir = out / "debug"
    if args.debug:
        debug_dir.mkdir(parents=True, exist_ok=True)

    (out / "labels.json").write_text(json.dumps({"id2label": ID2LABEL}, indent=2))

    image_id = 0
    annotation_id = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        install_asset_routes(page, library)
        for split, n in splits.items():
            with open(out / split / "metadata.jsonl", "w") as meta:
                for _ in range(n):
                    sample = random_sample(args.min_width, args.max_width, args.layout)
                    page.set_viewport_size({"width": sample.width, "height": 800})

                    html = render(sample, library)
                    load(page, html)
                    file_name = f"{image_id:05d}.png"
                    image_path = out / split / file_name
                    page.screenshot(path=str(image_path), full_page=True)
                    with Image.open(image_path) as img:
                        width, height = img.size
                    anns = extract_annotations(page, width, height)

                    objects: dict[str, list[Any]] = {"id": [], "bbox": [], "categories": [], "area": []}
                    for ann in anns:
                        objects["id"].append(annotation_id)
                        objects["bbox"].append(ann["bbox"])
                        objects["categories"].append(ann["category_id"])
                        objects["area"].append(round(ann["bbox"][2] * ann["bbox"][3], 2))
                        annotation_id += 1
                    meta.write(json.dumps({
                        "file_name": file_name,
                        "image_id": image_id,
                        "width": width,
                        "height": height,
                        "objects": objects,
                        **sample.describe(),
                    }, ensure_ascii=False) + "\n")

                    if args.debug:
                        stem = f"{image_id:05d}-{sample.layout.name}"
                        (debug_dir / f"{stem}.html").write_text(html)
                        draw_annotations(image_path, anns, debug_dir / f"{stem}-boxes.png")
                        html_seg = render(sample, library, segmented=True)
                        (debug_dir / f"{stem}-seg.html").write_text(html_seg)
                        load(page, html_seg)
                        page.screenshot(path=str(debug_dir / f"{stem}-seg.png"), full_page=True)

                    image_id += 1
                    if image_id % 50 == 0:
                        print(f"{image_id}/{args.count} images")
        browser.close()
    print(f"Wrote {image_id} images ({splits['train']} train / {splits['validation']} validation) to {out}")
