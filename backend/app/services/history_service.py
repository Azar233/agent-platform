"""User-scoped detection history queries."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import String, cast, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.entity.db_models import DetectionResult, DetectionScene, DetectionTask


class HistoryService:
    @staticmethod
    def list_tasks(
        db: Session,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 10,
        task_type: str | None = None,
        status: str | None = None,
        scene_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        keyword: str | None = None,
    ) -> dict:
        query = (
            db.query(DetectionTask)
            .join(DetectionScene, DetectionTask.scene_id == DetectionScene.id)
            .options(joinedload(DetectionTask.scene))
            .filter(DetectionTask.user_id == user_id)
        )
        if task_type:
            query = query.filter(DetectionTask.task_type == task_type)
        if status:
            query = query.filter(DetectionTask.status == status)
        if scene_id is not None:
            query = query.filter(DetectionTask.scene_id == scene_id)
        if start_date:
            query = query.filter(DetectionTask.created_at >= datetime.combine(start_date, time.min))
        if end_date:
            query = query.filter(
                DetectionTask.created_at < datetime.combine(end_date + timedelta(days=1), time.min)
            )
        keyword = (keyword or "").strip()
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    cast(DetectionTask.id, String).ilike(pattern),
                    DetectionScene.name.ilike(pattern),
                    DetectionScene.display_name.ilike(pattern),
                )
            )

        total = query.count()
        tasks = (
            query.order_by(desc(DetectionTask.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": [HistoryService._task_dict(task) for task in tasks],
        }

    @staticmethod
    def _task_dict(task: DetectionTask) -> dict:
        return {
            "id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "scene_id": task.scene_id,
            "scene_name": task.scene.display_name if task.scene else None,
            "total_images": task.total_images or 0,
            "total_objects": task.total_objects or 0,
            "total_inference_time": round(task.total_inference_time or 0, 2),
            "avg_inference_time": round(
                (task.total_inference_time or 0) / task.total_images, 2
            ) if task.total_images else 0.0,
            "conf_threshold": task.conf_threshold,
            "iou_threshold": task.iou_threshold,
            "error_message": task.error_message,
            "analysis_report": task.analysis_report,
            "analysis_suggestion": task.analysis_suggestion,
            "risk_level": task.risk_level,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    @staticmethod
    def get_task_detail(db: Session, user_id: int, task_id: int) -> dict | None:
        task = (
            db.query(DetectionTask)
            .options(joinedload(DetectionTask.scene))
            .filter(DetectionTask.id == task_id, DetectionTask.user_id == user_id)
            .first()
        )
        if not task:
            return None
        results = (
            db.query(DetectionResult)
            .filter(DetectionResult.task_id == task_id)
            .order_by(DetectionResult.id)
            .all()
        )
        class_counts: dict[str, int] = {}
        result_items = []
        for result in results:
            name = result.class_name_cn or result.class_name
            class_counts[name] = class_counts.get(name, 0) + 1
            result_items.append(
                {
                    "id": result.id,
                    "class_name": result.class_name,
                    "class_name_cn": result.class_name_cn,
                    "class_id": result.class_id,
                    "confidence": round(result.confidence, 4),
                    "bbox": result.bbox,
                    "image_path": result.image_path,
                    "annotated_image_url": result.annotated_image_url,
                    "inference_time": round(result.inference_time, 2)
                    if result.inference_time is not None
                    else None,
                    "image_width": result.image_width,
                    "image_height": result.image_height,
                }
            )
        return {
            "task": HistoryService._task_dict(task),
            "class_counts": class_counts,
            "results": result_items,
        }

    @staticmethod
    def delete_task(db: Session, user_id: int, task_id: int) -> bool:
        task = (
            db.query(DetectionTask)
            .filter(DetectionTask.id == task_id, DetectionTask.user_id == user_id)
            .first()
        )
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True

    @staticmethod
    def get_summary(db: Session, user_id: int) -> dict:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        total = (
            db.query(func.count(DetectionTask.id))
            .filter(DetectionTask.user_id == user_id)
            .scalar()
            or 0
        )
        today_count = (
            db.query(func.count(DetectionTask.id))
            .filter(DetectionTask.user_id == user_id, DetectionTask.created_at >= today)
            .scalar()
            or 0
        )
        rows = (
            db.query(DetectionTask.status, func.count(DetectionTask.id))
            .filter(DetectionTask.user_id == user_id)
            .group_by(DetectionTask.status)
            .all()
        )
        status_counts = {name: 0 for name in ("completed", "processing", "failed", "pending")}
        status_counts.update({status: int(count) for status, count in rows})
        return {
            "total_tasks": int(total),
            "today_tasks": int(today_count),
            "status_counts": status_counts,
        }

    @staticmethod
    def list_scenes(db: Session) -> list[dict]:
        scenes = (
            db.query(DetectionScene)
            .filter(DetectionScene.is_active.is_(True))
            .order_by(DetectionScene.display_name)
            .all()
        )
        return [
            {
                "id": scene.id,
                "name": scene.name,
                "display_name": scene.display_name,
                "category": scene.category,
            }
            for scene in scenes
        ]


history_service = HistoryService()
