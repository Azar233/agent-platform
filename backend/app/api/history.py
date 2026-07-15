"""Authenticated detection history endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.session import get_db
from app.services.history_service import history_service

router = APIRouter(prefix="/api/history", tags=["检测历史"])


@router.get("/tasks", summary="检测任务分页列表")
def list_detection_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    task_type: str | None = None,
    status: str | None = None,
    scene_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    keyword: str | None = Query(None, max_length=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="开始日期不能晚于结束日期")
    return history_service.list_tasks(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        task_type=task_type,
        status=status,
        scene_id=scene_id,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
    )


@router.get("/tasks/{task_id}", summary="检测任务详情")
def get_detection_task_detail(
    task_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = history_service.get_task_detail(db, current_user.id, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    return result


@router.delete("/tasks/{task_id}", summary="删除检测任务")
def delete_detection_task(
    task_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not history_service.delete_task(db, current_user.id, task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    return {"message": f"任务 #{task_id} 已删除", "task_id": task_id}


@router.get("/summary", summary="历史记录摘要")
def get_history_summary(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return history_service.get_summary(db, current_user.id)


@router.get("/scenes", summary="可用识别场景")
def list_scenes(
    _current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"scenes": history_service.list_scenes(db)}
