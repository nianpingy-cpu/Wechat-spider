"""统一日志服务 —— 消除 add_log 重复代码，增加 phase 支持"""
import asyncio
from datetime import datetime
from backend.database import SessionLocal
from backend.models import Task, TaskLog
from backend.ws_manager import manager


def add_log(task_id: int, level: str, message: str, phase: str = ""):
    """写入日志到数据库并广播 WebSocket。

    Args:
        task_id: 关联的任务 ID
        level: 日志级别 (info | success | warning | error)
        message: 日志内容
        phase: 阶段标签 (searching | fetching | crawling | stats | retry | pipeline)
    """
    db = SessionLocal()
    try:
        log_entry = TaskLog(
            task_id=task_id,
            level=level,
            message=message,
            phase=phase,
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        pass  # 日志写入失败不影响主流程
    finally:
        db.close()

    # WebSocket 广播（健壮版：处理事件循环未运行的情况）
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            manager.broadcast_sync(task_id, {
                "type": "log",
                "task_id": task_id,
                "level": level,
                "message": message,
                "phase": phase,
                "time": datetime.utcnow().strftime("%H:%M:%S"),
            })
    except RuntimeError:
        pass  # 无事件循环时不广播，但数据库已记录


def update_task_progress(task_id: int, success_count: int = None,
                         fail_count: int = None, total_count: int = None,
                         status: str = None):
    """更新任务进度并广播。

    集中处理 Task 表更新 + WebSocket 推送进度百分比。
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        if total_count is not None:
            task.total_count = total_count
        if success_count is not None:
            task.success_count = success_count
        if fail_count is not None:
            task.fail_count = fail_count
        if status is not None:
            task.status = status
        db.commit()

        # 广播进度更新
        pct = 0
        if task.total_count > 0:
            pct = round(task.success_count / task.total_count * 100, 1)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                manager.broadcast_sync(task_id, {
                    "type": "progress",
                    "task_id": task_id,
                    "success_count": task.success_count,
                    "fail_count": task.fail_count,
                    "total_count": task.total_count,
                    "percentage": pct,
                    "status": task.status,
                })
        except RuntimeError:
            pass
    except Exception:
        pass
    finally:
        db.close()
