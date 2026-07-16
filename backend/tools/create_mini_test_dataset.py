#!/usr/bin/env python3
"""
生成一个最小的 YOLO 检测数据集，用于验证 VisionPay Agent 的
「数据集构建 → 冻结 → 训练」完整流程。

图片是合成的（PIL 绘制），只有 smoke-test 意义，不能训练出可用模型。
"""
import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw


SPLITS = ["train", "val", "test"]
# 每个 split 每个类别生成几张图
IMAGES_PER_CLASS = {"train": 3, "val": 2, "test": 2}
CLASSES = ["apple", "banana", "orange"]
COLORS = {
    "apple": (220, 60, 60),      # 红
    "banana": (255, 220, 80),    # 黄
    "orange": (255, 150, 40),    # 橙
}
IMG_SIZE = 128


def make_image(class_name: str) -> Image.Image:
    """生成一张纯色背景、中间一个矩形的图片。"""
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    margin = int(IMG_SIZE * 0.2)
    draw.rectangle(
        [margin, margin, IMG_SIZE - margin, IMG_SIZE - margin],
        fill=COLORS[class_name],
        outline=(50, 50, 50),
        width=2,
    )
    return img


def create_dataset(output_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    names_yaml = "".join(f"  - {name}\n" for name in CLASSES)
    yaml_path = output_dir / "data.yaml"
    yaml_path.write_text(
        f"""path: {output_dir.as_posix()}
train: images/train
val: images/val
test: images/test
nc: {len(CLASSES)}
names:
{names_yaml}""",
        encoding="utf-8",
    )

    for split in SPLITS:
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

        for class_index, class_name in enumerate(CLASSES):
            for i in range(IMAGES_PER_CLASS[split]):
                stem = f"{split}_{class_name}_{i:02d}"
                img = make_image(class_name)
                img.save(output_dir / "images" / split / f"{stem}.jpg", quality=90)

                # 同一个框占图片中间 60% 区域，坐标已归一化
                label_path = output_dir / "labels" / split / f"{stem}.txt"
                label_path.write_text(
                    f"{class_index} 0.5 0.5 0.6 0.6\n",
                    encoding="utf-8",
                )

    print(f"已生成测试数据集: {output_dir}")
    print(f"类别数: {len(CLASSES)} -> {CLASSES}")
    print("目录结构:")
    for p in sorted(output_dir.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(output_dir)}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建最小 YOLO 测试数据集")
    parser.add_argument(
        "--output",
        default=os.environ.get("MINI_DATASET_DIR", "test-datasets/mini-visionpay"),
        help="输出目录（默认 test-datasets/mini-visionpay）",
    )
    args = parser.parse_args()
    create_dataset(Path(args.output))
