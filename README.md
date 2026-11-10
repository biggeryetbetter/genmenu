# genmenu

Generates synthetic restaurant-menu images with bounding-box annotations for fine-tuning YOLOS (`TrainingYOLOS.ipynb`) or Ultralytics YOLO (e.g. YOLO26).

```sh
uv run playwright install chromium   # once
uv run genmenu                       # 500 images, 80/20 train/validation split -> out/dataset
uv run genmenu --count 20 --debug    # also write HTML, CSS-segmented renders and box overlays to out/dataset/debug
uv run genmenu --layout poster --debug --count 5   # only one layout
uv run genmenu --images path/to/photos             # extra pictures for image layouts (default: assets/images if present)
uv run genmenu --format yolo                       # Ultralytics YOLO layout + data.yaml (default: --format hf)
uv run genmenu --help
```

Each `metadata.jsonl` row also records `layout`, `price_format`, `mode`, `scheme`, `heading_font` and `body_font`, so results can be broken down per style.

With `--format hf` (default), output is a Hugging Face object-detection `imagefolder` dataset (`train/` and `validation/`, each with PNGs and `metadata.jsonl`) plus `labels.json`:

| id | label | template class |
|---|---|---|
| 0 | title | `ann-title` |
| 1 | subtitle | `ann-subtitle` |
| 2 | menu_item | `ann-item` |
| 3 | item_title | `ann-item-title` |
| 4 | item_description | `ann-item-desc` |
| 5 | variant | `ann-variant` |
| 6 | variant_title | `ann-variant-title` |
| 7 | variant_price | `ann-variant-price` |
| 8 | item_price | `ann-item-price` |
| 9 | section_title | `ann-section-title` |

### Ultralytics YOLO format (`--format yolo`)

```
out/dataset/
  data.yaml              # path, train, val, names (same ids as the table above)
  images/{train,val}/*.png
  labels/{train,val}/*.txt   # one line per box: class x_center y_center width height (normalized 0-1)
  metadata.jsonl         # per-image style info (layout, fonts, ...) + split; not read by Ultralytics
```

```python
from ultralytics import YOLO
YOLO("yolo26n.pt").train(data="out/dataset/data.yaml", imgsz=1024)
```

Menu screenshots are wide (up to `--max-width`) and often several thousand pixels tall. Ultralytics letterboxes each one to `imgsz`, so small text boxes shrink a lot. Consider a larger `imgsz`, `rect=True`, or a smaller `--max-width`. `data.yaml` stores the absolute path of the output directory, so regenerate it (or edit `path:`) if you move the dataset.

## Code layout

| Module | Role |
|---|---|
| `menu_data.py` | Random menu content (sections, items, variants, badges, footer) |
| `theme.py` | Colour palettes with contrast checks; bundled fonts (`assets/fonts`, OFL/Apache licensed) |
| `clipart.py` | Theme-coloured SVG clipart and user image library (never annotated) |
| `templating.py` | Layout registry, price formats, rendering, asset routes for fonts/images |
| `annotations.py` | Label categories, box extraction, debug overlays and segmented CSS |
| `formats.py` | Output writers per `--format` (`hf`, `yolo`) |

To add a layout, create `src/genmenu/templates/menu-layout-N.html.jinja` extending `base.html.jinja`, style it with the theme variables (`--bg`, `--surface`, `--text`, `--muted`, `--border`, `--primary`, `--secondary`, `--accent`, `--on-primary`, `--font-heading`, `--font-body`, `--base-size`), tag elements with the `ann-*` classes above, and register it in `LAYOUTS` in `templating.py`. Keep all randomness in Python (menu data or the seeded `art` object), never in the template, so normal and `--debug` segmented renders match.
