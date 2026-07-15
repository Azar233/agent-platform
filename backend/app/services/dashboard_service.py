"""Dashboard queries for the authenticated user's retail detection activity."""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.entity.db_models import DetectionResult, DetectionScene, DetectionTask


class DashboardService:
    """Build chart-ready aggregates without owning the database session."""

    @staticmethod
    def _period_summary(db: Session, user_id: int, start: datetime, end: datetime) -> dict:
        row = (
            db.query(
                func.count(DetectionTask.id),
                func.coalesce(func.sum(DetectionTask.total_images), 0),
                func.coalesce(func.sum(DetectionTask.total_objects), 0),
                func.coalesce(func.sum(DetectionTask.total_inference_time), 0.0),
            )
            .filter(
                DetectionTask.user_id == user_id,
                DetectionTask.created_at >= start,
                DetectionTask.created_at < end,
            )
            .one()
        )
        tasks, images, objects, inference_total = row
        images = int(images or 0)
        inference_total = float(inference_total or 0)
        return {
            "total_tasks": int(tasks or 0),
            "total_images": images,
            "total_objects": int(objects or 0),
            # A task may contain many images or sampled video frames. Per-image
            # latency is therefore more meaningful than averaging task totals.
            "avg_inference_time": round(inference_total / images, 2) if images else 0.0,
        }

    @staticmethod
    def get_statistics(db: Session, user_id: int, days: int = 30) -> dict:
        now = datetime.now()
        start = now - timedelta(days=days)
        previous_start = start - timedelta(days=days)
        current = DashboardService._period_summary(db, user_id, start, now)
        previous = DashboardService._period_summary(db, user_id, previous_start, start)

        def growth(key: str) -> float:
            old = previous[key]
            new = current[key]
            if old == 0:
                return 100.0 if new > 0 else 0.0
            return round((new - old) / old * 100, 1)

        return {
            **current,
            "growth": {
                "tasks": growth("total_tasks"),
                "images": growth("total_images"),
                "objects": growth("total_objects"),
                "inference_time": growth("avg_inference_time"),
            },
            "period_days": days,
        }

    @staticmethod
    def get_trend(db: Session, user_id: int, days: int = 30) -> dict:
        now = datetime.now()
        first_day = (now - timedelta(days=days - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_expr = func.date(DetectionTask.created_at)
        rows = (
            db.query(
                day_expr.label("day"),
                func.count(DetectionTask.id).label("task_count"),
                func.coalesce(func.sum(DetectionTask.total_objects), 0).label("object_count"),
                func.coalesce(func.sum(DetectionTask.total_images), 0).label("image_count"),
            )
            .filter(
                DetectionTask.user_id == user_id,
                DetectionTask.created_at >= first_day,
            )
            .group_by(day_expr)
            .order_by(day_expr)
            .all()
        )
        by_day = {
            str(row.day): {
                "date": str(row.day),
                "task_count": int(row.task_count or 0),
                "object_count": int(row.object_count or 0),
                "image_count": int(row.image_count or 0),
            }
            for row in rows
        }
        trend = []
        for offset in range(days):
            key = (first_day + timedelta(days=offset)).strftime("%Y-%m-%d")
            trend.append(
                by_day.get(
                    key,
                    {"date": key, "task_count": 0, "object_count": 0, "image_count": 0},
                )
            )
        return {"trend": trend, "period_days": days}

    @staticmethod
    def get_class_distribution(db: Session, user_id: int, days: int = 30) -> dict:
        start = datetime.now() - timedelta(days=days)
        display_name = func.coalesce(DetectionResult.class_name_cn, DetectionResult.class_name)
        rows = (
            db.query(display_name.label("name"), func.count(DetectionResult.id).label("count"))
            .join(DetectionTask, DetectionResult.task_id == DetectionTask.id)
            .filter(
                DetectionTask.user_id == user_id,
                DetectionTask.created_at >= start,
            )
            .group_by(display_name)
            .order_by(func.count(DetectionResult.id).desc(), display_name.asc())
            .all()
        )
        return {
            "distribution": [{"name": row.name, "value": int(row.count)} for row in rows],
            "period_days": days,
        }

    @staticmethod
    def get_scene_distribution(db: Session, user_id: int, days: int = 30) -> dict:
        start = datetime.now() - timedelta(days=days)
        rows = (
            db.query(DetectionScene.display_name.label("name"), func.count(DetectionTask.id).label("count"))
            .join(DetectionScene, DetectionTask.scene_id == DetectionScene.id)
            .filter(
                DetectionTask.user_id == user_id,
                DetectionTask.created_at >= start,
            )
            .group_by(DetectionScene.display_name)
            .order_by(func.count(DetectionTask.id).desc(), DetectionScene.display_name.asc())
            .all()
        )
        return {
            "distribution": [{"name": row.name, "value": int(row.count)} for row in rows],
            "period_days": days,
        }

    @staticmethod
    def get_type_distribution(db: Session, user_id: int, days: int = 30) -> dict:
        start = datetime.now() - timedelta(days=days)
        rows = (
            db.query(DetectionTask.task_type.label("name"), func.count(DetectionTask.id).label("count"))
            .filter(
                DetectionTask.user_id == user_id,
                DetectionTask.created_at >= start,
            )
            .group_by(DetectionTask.task_type)
            .order_by(func.count(DetectionTask.id).desc(), DetectionTask.task_type.asc())
            .all()
        )
        labels = {
            "single": "单图识别",
            "batch": "批量识别",
            "folder": "文件夹识别",
            "zip": "ZIP 识别",
            "video": "视频识别",
            "camera": "实时摄像头",
        }
        return {
            "distribution": [
                {"name": labels.get(row.name, row.name), "value": int(row.count)} for row in rows
            ],
            "period_days": days,
        }


dashboard_service = DashboardService()
