"""商品价格管理 API"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.session import get_db
from app.entity.db_models import ProductPrice
from app.entity.schemas import ProductPriceCreate, ProductPriceResponse, ProductPriceUpdate

router = APIRouter(prefix="/api/prices", tags=["商品价格"])


@router.get("", response_model=list[ProductPriceResponse], summary="获取所有商品价格")
def list_prices(
    q: str | None = Query(None, description="按商品中文名或条码搜索"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """列出所有 SKU 的价格，按 category_id 排序；支持按中文名或条码搜索。"""
    query = db.query(ProductPrice)
    if q:
        keyword = f"%{q.strip()}%"
        query = query.filter(
            or_(
                ProductPrice.name.ilike(keyword),
                ProductPrice.barcode.ilike(keyword),
            )
        )
    return query.order_by(ProductPrice.category_id).all()


@router.get("/{category_id}", response_model=ProductPriceResponse, summary="获取单个商品价格")
def get_price(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据 category_id 查询单个商品价格。"""
    price = db.query(ProductPrice).filter(ProductPrice.category_id == category_id).first()
    if not price:
        raise HTTPException(status_code=404, detail="该商品未设置价格")
    return price


@router.post(
    "",
    response_model=ProductPriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建单个商品价格",
)
def create_price(
    payload: ProductPriceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建单个商品价格。category_id 不能已存在。"""
    existing = (
        db.query(ProductPrice)
        .filter(ProductPrice.category_id == payload.category_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"category_id={payload.category_id} 的商品已存在",
        )

    price = ProductPrice(**payload.model_dump())
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.put("/{category_id}", response_model=ProductPriceResponse, summary="更新单个商品价格")
def update_price(
    category_id: int,
    payload: ProductPriceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据 category_id 更新单个商品价格。"""
    price = db.query(ProductPrice).filter(ProductPrice.category_id == category_id).first()
    if not price:
        raise HTTPException(status_code=404, detail="该商品未设置价格")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(price, field, value)

    db.commit()
    db.refresh(price)
    return price


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除单个商品价格")
def delete_price(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据 category_id 删除单个商品价格。"""
    price = db.query(ProductPrice).filter(ProductPrice.category_id == category_id).first()
    if not price:
        raise HTTPException(status_code=404, detail="该商品未设置价格")

    db.delete(price)
    db.commit()
    return None


@router.post("/batch-delete", status_code=status.HTTP_200_OK, summary="批量删除商品价格")
def batch_delete_prices(
    category_ids: list[int],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据 category_id 列表批量删除商品价格。"""
    if not category_ids:
        raise HTTPException(status_code=400, detail="category_id 列表不能为空")

    deleted = (
        db.query(ProductPrice)
        .filter(ProductPrice.category_id.in_(category_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"message": "批量删除成功", "deleted": deleted}


@router.post("/batch", summary="批量设置商品价格")
def batch_set_prices(
    items: list[ProductPriceCreate],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量创建或更新商品价格。如果 category_id 已存在则更新，否则新增。"""
    for item in items:
        existing = (
            db.query(ProductPrice)
            .filter(ProductPrice.category_id == item.category_id)
            .first()
        )
        if existing:
            existing.unit_price = item.unit_price
            existing.sku_name = item.sku_name or existing.sku_name
            existing.name = item.name or existing.name
            existing.barcode = item.barcode or existing.barcode
            existing.currency = item.currency or existing.currency
        else:
            db.add(ProductPrice(**item.model_dump()))
    db.commit()
    return {"message": "价格设置成功", "count": len(items)}
