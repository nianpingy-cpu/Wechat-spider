"""文章浏览/搜索/导出 API"""
import os
import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Article
from backend.schemas import ArticleResponse, ArticleDetailResponse, ArticleListResponse, MessageResponse
from backend.config import BASE_DIR

router = APIRouter()


@router.get("/articles", response_model=ArticleListResponse)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """文章列表（分页 + 搜索 + 日期筛选）"""
    q = db.query(Article)

    if keyword:
        q = q.filter(Article.title.contains(keyword))
    if date_from:
        q = q.filter(Article.publish_date >= date_from)
    if date_to:
        q = q.filter(Article.publish_date <= date_to)

    total = q.count()
    items = q.order_by(Article.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()

    return ArticleListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/articles/{article_id}", response_model=ArticleDetailResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """获取文章详情（含 Markdown 正文）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return ArticleDetailResponse(
            id=0, title="", url="", file_path="", publish_date="",
            read_count=0, like_count=0, old_like_count=0, content="文章不存在"
        )
    content = ""
    if article.file_path and os.path.exists(article.file_path):
        try:
            with open(article.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = "无法读取文件内容"

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        url=article.url,
        file_path=article.file_path,
        publish_date=article.publish_date,
        read_count=article.read_count,
        like_count=article.like_count,
        old_like_count=article.old_like_count,
        task_id=article.task_id,
        created_at=article.created_at,
        content=content,
    )


@router.delete("/articles/{article_id}", response_model=MessageResponse)
def delete_article(article_id: int, db: Session = Depends(get_db)):
    """删除文章（数据库记录 + 本地文件）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return MessageResponse(success=False, message="文章不存在")

    # 删除本地文件
    if article.file_path and os.path.exists(article.file_path):
        try:
            os.remove(article.file_path)
        except Exception:
            pass

    db.delete(article)
    db.commit()
    return MessageResponse(message="文章已删除")


@router.get("/articles/export/csv")
def export_articles_csv(
    keyword: str = Query(None),
    db: Session = Depends(get_db),
):
    """导出文章列表为 CSV"""
    q = db.query(Article)
    if keyword:
        q = q.filter(Article.title.contains(keyword))
    articles = q.order_by(Article.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "标题", "URL", "发布日期", "阅读量", "点赞数", "在看数"])
    for a in articles:
        writer.writerow([a.id, a.title, a.url, a.publish_date, a.read_count, a.like_count, a.old_like_count])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles_export.csv"}
    )


@router.get("/articles/export/json")
def export_articles_json(
    keyword: str = Query(None),
    db: Session = Depends(get_db),
):
    """导出文章列表为 JSON"""
    import json
    q = db.query(Article)
    if keyword:
        q = q.filter(Article.title.contains(keyword))
    articles = q.order_by(Article.created_at.desc()).all()

    data = [
        {
            "id": a.id, "title": a.title, "url": a.url,
            "publish_date": a.publish_date, "read_count": a.read_count,
            "like_count": a.like_count, "old_like_count": a.old_like_count,
        }
        for a in articles
    ]
    return StreamingResponse(
        iter([json.dumps(data, ensure_ascii=False, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=articles_export.json"}
    )
