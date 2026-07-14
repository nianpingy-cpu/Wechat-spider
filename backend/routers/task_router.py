"""任务管理 API + WebSocket"""
import threading
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Task, TaskLog, Config
from backend.schemas import TaskCreate, TaskResponse, TaskListResponse, TaskLogResponse, MessageResponse
from backend.ws_manager import manager

router = APIRouter()


def _get_config_dict(db: Session) -> dict:
    configs = db.query(Config).all()
    return {c.key: c.value for c in configs}


@router.post("/tasks", response_model=TaskResponse)
def create_task(req: TaskCreate, db: Session = Depends(get_db)):
    """创建新任务"""
    task = Task(
        type=req.type,
        input_file=req.input_file,
        start_page=req.start_page,
        end_page=req.end_page,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """获取任务列表"""
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    total = q.count()
    items = q.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return TaskListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return TaskResponse(id=0, type="", status="not_found", input_file="",
                            start_page=0, end_page=0, total_count=0, success_count=0, fail_count=0)
    return task


@router.post("/tasks/{task_id}/start", response_model=MessageResponse)
def start_task(task_id: int, db: Session = Depends(get_db)):
    """启动任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return MessageResponse(success=False, message="任务不存在")

    if task.status == "running":
        return MessageResponse(success=False, message="任务已在运行中")

    cfg = _get_config_dict(db)
    token = cfg.get("token", "")
    cookie = cfg.get("cookie", "")
    appmsg_token = cfg.get("appmsg_token", "")
    target_name = cfg.get("target_name", "")

    if task.type == "fetch_urls":
        if not token or not cookie:
            return MessageResponse(success=False, message="请先在配置页填写 Token 和 Cookie")
        from services.url_fetcher_service import fetch_urls
        thread = threading.Thread(
            target=fetch_urls,
            args=(task_id, token, cookie, target_name,
                  task.start_page, task.end_page, task.input_file or f"url_({task.start_page}-{task.end_page}).txt"),
            daemon=True,
        )
        thread.start()
    elif task.type == "crawl_articles":
        if not cookie:
            return MessageResponse(success=False, message="请先在配置页填写 Cookie")
        from services.crawler_service import crawl_articles
        thread = threading.Thread(
            target=crawl_articles,
            args=(task_id, cookie, appmsg_token, task.input_file),
            daemon=True,
        )
        thread.start()
    else:
        return MessageResponse(success=False, message=f"未知任务类型: {task.type}")

    return MessageResponse(message=f"任务 {task_id} 已启动")


@router.post("/tasks/{task_id}/pause", response_model=MessageResponse)
def pause_task(task_id: int, db: Session = Depends(get_db)):
    """暂停任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return MessageResponse(success=False, message="任务不存在")
    if task.status != "running":
        return MessageResponse(success=False, message="任务未在运行中")
    task.status = "paused"
    db.commit()
    return MessageResponse(message="任务已暂停")


@router.post("/tasks/{task_id}/retry-failed", response_model=MessageResponse)
def retry_failed(task_id: int, db: Session = Depends(get_db)):
    """重试失败链接（读取 url_wrong.txt）"""
    import os
    from backend.config import BASE_DIR

    wrong_file = os.path.join(BASE_DIR, "url_wrong.txt")
    if not os.path.exists(wrong_file):
        return MessageResponse(success=False, message="没有失败链接文件 (url_wrong.txt)")

    # 创建新的爬取任务，以 url_wrong.txt 为输入
    task = Task(type="crawl_articles", input_file="url_wrong.txt")
    db.add(task)
    db.commit()
    db.refresh(task)

    cfg = _get_config_dict(db)
    cookie = cfg.get("cookie", "")
    appmsg_token = cfg.get("appmsg_token", "")

    from services.crawler_service import crawl_articles
    thread = threading.Thread(
        target=crawl_articles,
        args=(task.id, cookie, appmsg_token, "url_wrong.txt"),
        daemon=True,
    )
    thread.start()

    return MessageResponse(message=f"重试任务 {task.id} 已创建并启动")


@router.get("/tasks/{task_id}/logs", response_model=list[TaskLogResponse])
def get_task_logs(task_id: int, limit: int = Query(200, ge=1, le=1000),
                  db: Session = Depends(get_db)):
    """获取任务日志"""
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id) \
        .order_by(TaskLog.created_at.desc()).limit(limit).all()
    return list(reversed(logs))


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务及其日志"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return MessageResponse(success=False, message="任务不存在")
    if task.status == "running":
        return MessageResponse(success=False, message="不能删除正在运行的任务，请先暂停")
    # 删除关联日志
    db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return MessageResponse(message="任务已删除")


# ==================== WebSocket ====================

@router.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    await manager.connect(task_id, websocket)
    try:
        while True:
            # 保持连接，等待客户端消息（用于心跳）
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
