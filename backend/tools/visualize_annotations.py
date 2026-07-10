"""YOLO dataset annotation visualization utility.

Features:
    1. Draw YOLO-format bounding boxes and class labels on images.
    2. Randomly sample images or visualize one specified image.
    3. Export annotated images to files or show them in OpenCV windows.
    4. Generate a 4x4 overview grid.

Usage:
    cd backend

    python tools/visualize_annotations.py
    python tools/visualize_annotations.py --count 10
    python tools/visualize_annotations.py --output datasets/vision_pay/vis_output --count 10
    python tools/visualize_annotations.py --image train/000001.jpg --output datasets/vision_pay/vis_output
    python tools/visualize_annotations.py --grid --output datasets/vision_pay/vis_output/overview.jpg
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "datasets" / "vision_pay"
DEFAULT_OUTPUT_DIR = DEFAULT_DATASET_DIR / "vis_output"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
OUTPUT_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

COLORS = [
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (128, 255, 0),
    (255, 128, 0),
    (0, 128, 255),
    (128, 0, 255),
    (255, 255, 128),
    (128, 255, 255),
    (255, 128, 255),
    (0, 128, 128),
    (128, 0, 128),
    (128, 128, 0),
    (64, 255, 64),
    (255, 64, 64),
    (64, 64, 255),
    (255, 200, 0),
]


def load_class_names(dataset_dir: str | Path) -> dict[int, str]:
    """Load class names from data.yaml without requiring a YAML dependency."""

    yaml_path = Path(dataset_dir) / "data.yaml"
    if not yaml_path.exists():
        return {}

    names: dict[int, str] = {}
    in_names = False
    with yaml_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("names:"):
                in_names = True
                inline_value = stripped.split(":", 1)[1].strip()
                if inline_value.startswith("[") and inline_value.endswith("]"):
                    values = [
                        item.strip().strip("'\"")
                        for item in inline_value.strip("[]").split(",")
                        if item.strip()
                    ]
                    return {index: value for index, value in enumerate(values)}
                continue

            if not in_names:
                continue

            if raw_line[:1] not in {" ", "\t"}:
                break

            if ":" in stripped:
                key, value = stripped.split(":", 1)
                try:
                    class_id = int(key.strip())
                except ValueError:
                    continue
                names[class_id] = value.strip().strip("'\"")
            elif stripped.startswith("-"):
                names[len(names)] = stripped[1:].strip().strip("'\"")

    return names


def draw_yolo_annotations(
    image: np.ndarray,
    label_file: str | Path,
    class_names: dict[int, str],
    thickness: int = 2,
    font_scale: float = 0.6,
) -> np.ndarray:
    """Draw YOLO-format labels on an OpenCV BGR image."""

    img_h, img_w = image.shape[:2]
    label_path = Path(label_file)
    if not label_path.exists():
        return image

    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        parts = raw_line.strip().split()
        if len(parts) != 5:
            continue

        try:
            class_id = int(parts[0])
            x_center, y_center, width, height = [float(value) for value in parts[1:]]
        except ValueError:
            continue

        x1 = int((x_center - width / 2) * img_w)
        y1 = int((y_center - height / 2) * img_h)
        x2 = int((x_center + width / 2) * img_w)
        y2 = int((y_center + height / 2) * img_h)

        x1 = max(0, min(x1, img_w - 1))
        y1 = max(0, min(y1, img_h - 1))
        x2 = max(0, min(x2, img_w - 1))
        y2 = max(0, min(y2, img_h - 1))
        if x2 <= x1 or y2 <= y1:
            continue

        color = COLORS[class_id % len(COLORS)]
        label_text = class_names.get(class_id, f"class_{class_id}")

        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

        (text_w, text_h), _baseline = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
        )
        label_y = max(y1, text_h + 10)
        cv2.rectangle(
            image,
            (x1, label_y - text_h - 10),
            (x1 + text_w + 4, label_y),
            color,
            -1,
        )
        cv2.putText(
            image,
            label_text,
            (x1 + 2, label_y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return image


def collect_image_label_pairs(
    dataset_dir: str | Path,
    splits: list[str] | None = None,
) -> list[tuple[Path, Path, str, str]]:
    """Collect image and YOLO label file pairs from the dataset."""

    dataset_path = Path(dataset_dir)
    if splits is None:
        splits = ["train", "val", "test"]

    pairs: list[tuple[Path, Path, str, str]] = []
    for split in splits:
        image_dir = dataset_path / "images" / split
        label_dir = dataset_path / "labels" / split
        if not image_dir.exists():
            continue

        for image_file in sorted(image_dir.iterdir()):
            if not image_file.is_file() or image_file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            label_file = label_dir / f"{image_file.stem}.txt"
            pairs.append((image_file, label_file, split, image_file.name))

    return pairs


def annotate_image(
    image_path: Path,
    label_path: Path,
    split: str,
    filename: str,
    class_names: dict[int, str],
    thickness: int = 2,
    font_scale: float = 0.6,
) -> np.ndarray | None:
    """Read one image and return an annotated copy."""

    image = cv2.imread(str(image_path))
    if image is None:
        return None

    annotated = draw_yolo_annotations(
        image,
        label_path,
        class_names,
        thickness=thickness,
        font_scale=font_scale,
    )
    cv2.putText(
        annotated,
        f"split: {split} | file: {filename}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return annotated


def write_image(output_path: Path, image: np.ndarray) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image):
        raise RuntimeError(f"Failed to write image: {output_path}")


def resolve_single_output_path(output: str | Path, split: str, filename: str) -> Path:
    output_path = Path(output)
    if output_path.suffix.lower() in OUTPUT_IMAGE_EXTENSIONS:
        return output_path
    return output_path / f"vis_{split}_{filename}"


def visualize_random_samples(
    dataset_dir: str | Path,
    output_dir: str | Path | None = None,
    count: int = 5,
    splits: list[str] | None = None,
    class_names: dict[int, str] | None = None,
    seed: int | None = None,
) -> int:
    """Randomly sample images and visualize annotations."""

    if class_names is None:
        class_names = load_class_names(dataset_dir)

    pairs = collect_image_label_pairs(dataset_dir, splits)
    if not pairs:
        print("[error] No image-label pairs found.")
        return 1

    rng = random.Random(seed)
    samples = rng.sample(pairs, min(count, len(pairs)))
    print(f"Found {len(pairs)} images, visualizing {len(samples)} sample(s).")

    for image_path, label_path, split, filename in samples:
        annotated = annotate_image(image_path, label_path, split, filename, class_names)
        if annotated is None:
            print(f"  [skip] Cannot read image: {image_path}")
            continue

        if output_dir:
            out_path = Path(output_dir) / f"vis_{split}_{filename}"
            write_image(out_path, annotated)
            print(f"  [saved] {out_path}")
        else:
            window_name = f"[{split}] {filename}"
            cv2.imshow(window_name, annotated)
            print(f"  [show] {filename}; press any key for next, q to quit")
            key = cv2.waitKey(0) & 0xFF
            cv2.destroyAllWindows()
            if key == ord("q"):
                break

    return 0


def visualize_single_image(
    dataset_dir: str | Path,
    image_relpath: str,
    output_path: str | Path | None = None,
    class_names: dict[int, str] | None = None,
) -> int:
    """Visualize one specified image using a path like train/000001.jpg."""

    dataset_path = Path(dataset_dir)
    if class_names is None:
        class_names = load_class_names(dataset_path)

    normalized = image_relpath.replace("\\", "/")
    parts = normalized.split("/")
    if len(parts) < 2:
        print("[error] Use a path with split name, for example: train/000001.jpg")
        return 1

    split = parts[0]
    filename = parts[-1]
    image_path = dataset_path / "images" / split / filename
    label_path = dataset_path / "labels" / split / f"{Path(filename).stem}.txt"

    if not image_path.exists():
        print(f"[error] Image not found: {image_path}")
        return 1

    annotated = annotate_image(image_path, label_path, split, filename, class_names)
    if annotated is None:
        print(f"[error] Cannot read image: {image_path}")
        return 1

    if output_path:
        out_path = resolve_single_output_path(output_path, split, filename)
        write_image(out_path, annotated)
        print(f"Saved to: {out_path}")
    else:
        cv2.imshow(f"[{split}] {filename}", annotated)
        print(f"Showing {filename}; press any key to close")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 0


def resolve_grid_output_path(output: str | Path | None) -> Path:
    if output is None:
        return DEFAULT_OUTPUT_DIR / "overview.jpg"

    output_path = Path(output)
    if output_path.suffix.lower() in OUTPUT_IMAGE_EXTENSIONS:
        return output_path
    return output_path / "overview.jpg"


def generate_overview_grid(
    dataset_dir: str | Path,
    output_path: str | Path,
    grid_size: tuple[int, int] = (4, 4),
    splits: list[str] | None = None,
    class_names: dict[int, str] | None = None,
    seed: int | None = None,
) -> int:
    """Generate one overview image containing multiple annotated thumbnails."""

    if class_names is None:
        class_names = load_class_names(dataset_dir)

    pairs = collect_image_label_pairs(dataset_dir, splits)
    if not pairs:
        print("[error] No image-label pairs found.")
        return 1

    rows, cols = grid_size
    total_cells = rows * cols
    rng = random.Random(seed)
    samples = rng.sample(pairs, min(total_cells, len(pairs)))

    thumb_w, thumb_h = 400, 300
    grid_img = np.zeros((rows * thumb_h, cols * thumb_w, 3), dtype=np.uint8)

    for idx, (image_path, label_path, split, filename) in enumerate(samples):
        row = idx // cols
        col = idx % cols

        annotated = annotate_image(
            image_path,
            label_path,
            split,
            filename,
            class_names,
            thickness=1,
            font_scale=0.4,
        )
        if annotated is None:
            continue

        thumb = cv2.resize(annotated, (thumb_w, thumb_h))
        cv2.putText(
            thumb,
            f"{split}/{filename[:20]}",
            (5, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

        y_start = row * thumb_h
        x_start = col * thumb_w
        grid_img[y_start : y_start + thumb_h, x_start : x_start + thumb_w] = thumb

    out_path = Path(output_path)
    write_image(out_path, grid_img)
    print(f"Overview grid saved to: {out_path}")
    print(f"  grid: {rows} x {cols}, images: {len(samples)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YOLO dataset annotation visualization utility.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python tools/visualize_annotations.py
  python tools/visualize_annotations.py --count 10
  python tools/visualize_annotations.py --output datasets/vision_pay/vis_output --count 10
  python tools/visualize_annotations.py --image train/000001.jpg
  python tools/visualize_annotations.py --image train/000001.jpg --output datasets/vision_pay/vis_output
  python tools/visualize_annotations.py --grid --output datasets/vision_pay/vis_output/overview.jpg

Default dataset:
  {DEFAULT_DATASET_DIR}
""",
    )
    parser.add_argument(
        "--dataset",
        "-d",
        default=str(DEFAULT_DATASET_DIR),
        help="YOLO dataset directory.",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=5,
        help="Random sample count.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory, or output image path for --image/--grid.",
    )
    parser.add_argument(
        "--image",
        "-i",
        default=None,
        help="Image relative path with split name, for example train/000001.jpg.",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Generate a 4x4 overview grid image.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        help="Dataset splits to visualize.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible samples.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = Path(args.dataset)
    if not dataset_dir.exists():
        print(f"[error] Dataset directory does not exist: {dataset_dir}")
        return 1

    class_names = load_class_names(dataset_dir)
    if class_names:
        print(f"Loaded {len(class_names)} class(es).")
    else:
        print("[warning] data.yaml class names not found; using class IDs.")

    if args.grid:
        return generate_overview_grid(
            dataset_dir=dataset_dir,
            output_path=resolve_grid_output_path(args.output),
            grid_size=(4, 4),
            splits=args.splits,
            class_names=class_names,
            seed=args.seed,
        )

    if args.image:
        return visualize_single_image(
            dataset_dir=dataset_dir,
            image_relpath=args.image,
            output_path=args.output,
            class_names=class_names,
        )

    return visualize_random_samples(
        dataset_dir=dataset_dir,
        output_dir=args.output,
        count=args.count,
        splits=args.splits,
        class_names=class_names,
        seed=args.seed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
