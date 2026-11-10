"""Dataset writers: one per on-disk output format (selected with --format)."""
import json
from pathlib import Path
from typing import Any, Protocol, TextIO

from .annotations import ID2LABEL

# Logical split names used by the generator loop.
SPLITS = ("train", "validation")


class DatasetWriter(Protocol):
    def image_path(self, split: str, file_name: str) -> Path:
        """Where the screenshot for this image should be saved."""
        ...

    def write(self, split: str, file_name: str, image_id: int, width: int, height: int,
              anns: list[dict[str, Any]], extra: dict[str, Any]) -> None:
        """Record annotations (COCO-style pixel bboxes) and extra per-image metadata."""
        ...

    def close(self) -> None: ...


class HFWriter:
    """Hugging Face object-detection `imagefolder`: <split>/*.png + <split>/metadata.jsonl + labels.json."""

    def __init__(self, out: Path) -> None:
        self.out = out
        self.annotation_id = 0
        self.meta: dict[str, TextIO] = {}
        for split in SPLITS:
            (out / split).mkdir(parents=True, exist_ok=True)
            self.meta[split] = open(out / split / "metadata.jsonl", "w")
        (out / "labels.json").write_text(json.dumps({"id2label": ID2LABEL}, indent=2))

    def image_path(self, split: str, file_name: str) -> Path:
        return self.out / split / file_name

    def write(self, split: str, file_name: str, image_id: int, width: int, height: int,
              anns: list[dict[str, Any]], extra: dict[str, Any]) -> None:
        objects: dict[str, list[Any]] = {"id": [], "bbox": [], "categories": [], "area": []}
        for ann in anns:
            objects["id"].append(self.annotation_id)
            objects["bbox"].append(ann["bbox"])
            objects["categories"].append(ann["category_id"])
            objects["area"].append(round(ann["bbox"][2] * ann["bbox"][3], 2))
            self.annotation_id += 1
        self.meta[split].write(json.dumps({
            "file_name": file_name,
            "image_id": image_id,
            "width": width,
            "height": height,
            "objects": objects,
            **extra,
        }, ensure_ascii=False) + "\n")

    def close(self) -> None:
        for f in self.meta.values():
            f.close()


class YoloWriter:
    """Ultralytics YOLO detect format: images/<s>/*.png, labels/<s>/*.txt (normalized cx cy w h), data.yaml."""

    SPLIT_DIRS = {"train": "train", "validation": "val"}

    def __init__(self, out: Path) -> None:
        self.out = out
        for d in self.SPLIT_DIRS.values():
            (out / "images" / d).mkdir(parents=True, exist_ok=True)
            (out / "labels" / d).mkdir(parents=True, exist_ok=True)
        # Ultralytics label files can't carry style info, so keep it in a side file.
        self.meta = open(out / "metadata.jsonl", "w")

    def image_path(self, split: str, file_name: str) -> Path:
        return self.out / "images" / self.SPLIT_DIRS[split] / file_name

    def write(self, split: str, file_name: str, image_id: int, width: int, height: int,
              anns: list[dict[str, Any]], extra: dict[str, Any]) -> None:
        lines = []
        for ann in anns:
            x, y, w, h = ann["bbox"]
            lines.append(f"{ann['category_id']} {(x + w / 2) / width:.6f} {(y + h / 2) / height:.6f}"
                         f" {w / width:.6f} {h / height:.6f}\n")
        label_path = self.out / "labels" / self.SPLIT_DIRS[split] / Path(file_name).with_suffix(".txt")
        label_path.write_text("".join(lines))
        self.meta.write(json.dumps({
            "file_name": file_name,
            "split": self.SPLIT_DIRS[split],
            "image_id": image_id,
            "width": width,
            "height": height,
            **extra,
        }, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self.meta.close()
        names = "\n".join(f"  {i}: {json.dumps(name) if not name.isidentifier() else name}"
                          for i, name in ID2LABEL.items())
        (self.out / "data.yaml").write_text(
            f"path: {json.dumps(str(self.out.resolve()))}\n"
            f"train: images/{self.SPLIT_DIRS['train']}\n"
            f"val: images/{self.SPLIT_DIRS['validation']}\n"
            f"names:\n{names}\n"
        )


WRITERS: dict[str, type[HFWriter] | type[YoloWriter]] = {"hf": HFWriter, "yolo": YoloWriter}
