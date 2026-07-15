"""Profile settings and administrator-only user/role queries."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.session import get_db
from app.entity.schemas import ChangePassword, UserUpdate
from app.services.user_service import user_service

router = APIRouter(prefix="/api/user", tags=["用户管理"])


def require_admin(current_user=Depends(get_current_user)):
    if not user_service.is_admin(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可查询用户与权限信息")
    return current_user


@router.get("/list", summary="用户列表（管理员）")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.list_users(db, page=page, page_size=page_size, keyword=keyword)


@router.get("/roles", summary="角色列表（管理员）")
def list_roles(
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {"roles": user_service.list_roles(db)}


@router.put("/profile", summary="更新个人信息")
def update_profile(
    request: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    changes = request.model_dump(exclude_unset=True)
    return user_service.update_profile(db, current_user.id, **changes)


@router.put("/password", summary="修改密码")
def change_password(
    request: ChangePassword,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.change_password(
        db,
        current_user.id,
        old_password=request.old_password,
        new_password=request.new_password,
    )


@router.get("/{user_id}", summary="用户详情（管理员）")
def get_user_detail(
    user_id: int,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.serialize_user(user_service.get_user_by_id(db, user_id))
