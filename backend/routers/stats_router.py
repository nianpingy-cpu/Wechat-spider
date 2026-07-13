"""统计看板 API"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Article, Task
from backend.schemas import StatsOverview, DailyStats, TopReadArticle

router = APIRouter()


@router.get("/stats/overview", response_model=StatsOverview)
def get_overview(db: Session = Depends(get_db)):
    """总览统计"""
    total_articles = db.query(func.count(Article.id)).scalar() or 0
    total_reads = db.query(func.sum(Article.read_count)).scalar() or 0
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == "completed").scalar() or 0
    running_tasks = db.query(func.count(Task.id)).filter(Task.status == "running").scalar() or 0

    return StatsOverview(
        total_articles=total_articles,
        total_reads=total_reads,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        running_tasks=running_tasks,
    )


@router.get("/stats/daily", response_model=list[DailyStats])
def get_daily_stats(db: Session = Depends(get_db)):
    """按日期统计文章数量"""
    results = db.query(
        Article.publish_date,
        func.count(Article.id)
    ).group_by(Article.publish_date).order_by(Article.publish_date).all()

    return [DailyStats(date=r[0] or "未知", count=r[1]) for r in results]


@router.get("/stats/top-read", response_model=list[TopReadArticle])
def get_top_read(limit: int = 10, db: Session = Depends(get_db)):
    """阅读量 Top N 文章"""
    articles = db.query(Article).order_by(Article.read_count.desc()).limit(limit).all()
    return [
        TopReadArticle(id=a.id, title=a.title, read_count=a.read_count, publish_date=a.publish_date)
        for a in articles
    ]
