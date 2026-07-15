"""Dataset-version scoped product price management API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.session import get_db
from app.entity.db_models import DatasetClassMapping, DatasetVersion, Product, ProductPrice
from app.entity.schemas import DatasetProductPriceResponse, ProductPriceUpdate

router = APIRouter(prefix="/api/prices", tags=["商品价格"])


def _dataset(db: Session, dataset_version_id: int) -> DatasetVersion:
    dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="数据集版本不存在")
    return dataset


def _mapping(db: Session, dataset_version_id: int, product_id: int) -> DatasetClassMapping:
    _dataset(db, dataset_version_id)
    mapping = (
        db.query(DatasetClassMapping)
        .filter(
            DatasetClassMapping.dataset_version_id == dataset_version_id,
            DatasetClassMapping.product_id == product_id,
        )
        .first()
    )
    if mapping is None:
        raise HTTPException(status_code=404, detail="该商品不属于所选数据集版本")
    return mapping


def _price_for_mapping(db: Session, mapping: DatasetClassMapping) -> ProductPrice | None:
    price = (
        db.query(ProductPrice)
        .filter(ProductPrice.product_id == mapping.product_id)
        .first()
    )
    if price is not None or mapping.category_id is None:
        return price
    legacy = (
        db.query(ProductPrice)
        .filter(ProductPrice.category_id == mapping.category_id)
        .first()
    )
    if legacy is not None and legacy.product_id in {None, mapping.product_id}:
        return legacy
    return None


def _serialize(
    db: Session,
    mapping: DatasetClassMapping,
    price: ProductPrice | None = None,
) -> dict:
    price = price if price is not None else _price_for_mapping(db, mapping)
    product = (
        db.query(Product).filter(Product.id == mapping.product_id).first()
        if mapping.product_id is not None
        else None
    )
    return {
        "dataset_version_id": mapping.dataset_version_id,
        "mapping_id": mapping.id,
        "class_index": mapping.class_index,
        "product_id": mapping.product_id,
        "product_key": mapping.product_key,
        "category_id": price.category_id if price is not None else mapping.category_id,
        "class_name": mapping.class_name,
        "display_name": mapping.display_name,
        "price_id": price.id if price is not None else None,
        "sku_name": price.sku_name if price is not None else getattr(product, "sku_name", None),
        "name": price.name if price is not None else (
            getattr(product, "name", None) or mapping.display_name
        ),
        "barcode": price.barcode if price is not None else getattr(product, "barcode", None),
        "unit_price": price.unit_price if price is not None else None,
        "currency": (price.currency if price is not None else None) or "CNY",
        "has_price": price is not None,
        "created_at": price.created_at if price is not None else None,
        "updated_at": price.updated_at if price is not None else None,
    }


@router.get("", response_model=list[DatasetProductPriceResponse], summary="获取数据集版本价目表")
def list_prices(
    dataset_version_id: int = Query(..., ge=1, description="要管理的数据集版本 ID"),
    q: str | None = Query(None, description="按商品名称、类别、条码或稳定 ID 搜索"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Only return products already mapped by the selected dataset version."""
    del current_user
    _dataset(db, dataset_version_id)
    mappings = (
        db.query(DatasetClassMapping)
        .filter(DatasetClassMapping.dataset_version_id == dataset_version_id)
        .order_by(DatasetClassMapping.class_index)
        .all()
    )
    rows = [_serialize(db, mapping) for mapping in mappings if mapping.product_id is not None]
    keyword = (q or "").strip().lower()
    if not keyword:
        return rows
    searchable_fields = (
        "product_id",
        "product_key",
        "class_index",
        "class_name",
        "display_name",
        "sku_name",
        "name",
        "barcode",
    )
    return [
        row
        for row in rows
        if any(keyword in str(row.get(field) or "").lower() for field in searchable_fields)
    ]


@router.get(
    "/{product_id}",
    response_model=DatasetProductPriceResponse,
    summary="获取数据集版本中的单个商品价格",
)
def get_price(
    product_id: int,
    dataset_version_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    mapping = _mapping(db, dataset_version_id, product_id)
    return _serialize(db, mapping)


@router.put(
    "/{product_id}",
    response_model=DatasetProductPriceResponse,
    summary="更新数据集版本中已有商品的价格",
)
def update_price(
    product_id: int,
    payload: ProductPriceUpdate,
    dataset_version_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a stable product only after proving it belongs to the selected dataset."""
    del current_user
    mapping = _mapping(db, dataset_version_id, product_id)
    price = _price_for_mapping(db, mapping)
    values = payload.model_dump(exclude_unset=True)
    if price is None:
        if values.get("unit_price") is None:
            raise HTTPException(status_code=400, detail="该商品尚未设置价格，请填写单价")
        category_id = mapping.category_id
        category_in_use = (
            db.query(ProductPrice)
            .filter(ProductPrice.category_id == category_id)
            .first()
            if category_id is not None
            else None
        )
        if category_id is None or category_in_use is not None:
            category_id = int(db.query(func.max(ProductPrice.category_id)).scalar() or 0) + 1
        product = db.query(Product).filter(Product.id == product_id).first()
        price = ProductPrice(
            product_id=product_id,
            category_id=category_id,
            sku_name=values.get("sku_name") or getattr(product, "sku_name", None) or mapping.class_name,
            name=values.get("name") or getattr(product, "name", None) or mapping.display_name,
            barcode=values.get("barcode") or getattr(product, "barcode", None),
            unit_price=values["unit_price"],
            currency=values.get("currency") or "CNY",
        )
        db.add(price)
    else:
        if price.product_id is None:
            price.product_id = product_id
        for field, value in values.items():
            setattr(price, field, value)

    db.commit()
    db.refresh(price)
    return _serialize(db, mapping, price)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清除数据集版本中已有商品的价格配置",
)
def delete_price(
    product_id: int,
    dataset_version_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete only the price record; the stable product and dataset mapping remain intact."""
    del current_user
    mapping = _mapping(db, dataset_version_id, product_id)
    price = _price_for_mapping(db, mapping)
    if price is None:
        raise HTTPException(status_code=404, detail="该商品尚未设置价格")
    db.delete(price)
    db.commit()
    return None
