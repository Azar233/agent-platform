"""批量导入 200 个 SKU 的初始价格。

价格根据商品大类（sku_class）设置，具体策略见 PRICE_MAP。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 将 backend 根目录加入 Python 路径
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database.session import SessionLocal
from app.entity.db_models import ProductPrice

# 按商品大类设置的默认单价（元）
PRICE_MAP = {
    "puffed_food": 4.0,
    "dried_fruit": 8.5,
    "dried_food": 7.0,
    "instant_drink": 6.0,
    "instant_noodles": 4.5,
    "dessert": 6.0,
    "drink": 3.5,
    "alcohol": 6.0,
    "milk": 4.0,
    "canned_food": 5.5,
    "chocolate": 7.0,
    "gum": 5.0,
    "candy": 3.5,
    "seasoner": 4.5,
    "personal_hygiene": 12.0,
    "tissue": 8.0,
    "stationery": 5.0,
}


def load_sku_info(json_path: Path) -> dict[int, dict]:
    """从 instances_train2019.json 读取 SKU 信息。"""
    with open(json_path, "rb") as f:
        raw = f.read()

    text = raw.decode("utf-8", errors="ignore")
    # 兼容文件末尾可能存在的多余字符
    for i in range(len(text), 0, -1):
        try:
            data = json.loads(text[:i])
            break
        except json.JSONDecodeError:
            continue

    return {item["category_id"]: item for item in data["__raw_Chinese_name_df"]}


def main() -> int:
    json_path = BACKEND_ROOT.parent / "instances_train2019.json"
    if not json_path.exists():
        print(f"[error] SKU 信息文件不存在: {json_path}")
        return 1

    sku_map = load_sku_info(json_path)
    print(f"Loaded {len(sku_map)} SKU definitions from {json_path}")

    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for category_id, info in sku_map.items():
            sku_class = info.get("sku_class", "")
            unit_price = PRICE_MAP.get(sku_class, 0.0)

            existing = (
                db.query(ProductPrice)
                .filter(ProductPrice.category_id == category_id)
                .first()
            )
            if existing:
                existing.unit_price = unit_price
                existing.sku_name = info.get("sku_name")
                existing.name = info.get("name")
                existing.barcode = str(info.get("code", ""))
                updated += 1
            else:
                db.add(
                    ProductPrice(
                        category_id=category_id,
                        sku_name=info.get("sku_name"),
                        name=info.get("name"),
                        barcode=str(info.get("code", "")),
                        unit_price=unit_price,
                    )
                )
                created += 1

        db.commit()
        print(f"Price import complete: created={created}, updated={updated}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"[error] Failed to import prices: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
