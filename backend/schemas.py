"""Pydantic 请求/响应 Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ==================== Config ====================

class ConfigItem(BaseModel):
    key: str
    value: str

class ConfigUpdateRequest(BaseModel):
    items: list[ConfigItem]

class ConfigResponse(BaseModel):
    id: int
    key: str
    value: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Task ====================

class TaskCreate(BaseModel):
    type: str  # fetch_urls | crawl_content | fetch_stats | full_pipeline
    input_file: str = ""
    start_page: int = 1
    end_page: int = 1
    parent_task_id: Optional[int] = None
    batch_id: str = ""
    article_ids: Optional[list[int]] = None  # fetch_stats 指定文章 ID 列表

class TaskResponse(BaseModel):
    id: int
    type: str
    status: str
    input_file: str
    start_page: int
    end_page: int
    total_count: int
    success_count: int
    fail_count: int
    parent_task_id: Optional[int] = None
    batch_id: str = ""
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int

class BatchGroup(BaseModel):
    """批次中所有任务按类型分组"""
    batch_id: str
    tasks: list[TaskResponse]

class BatchListResponse(BaseModel):
    groups: list[BatchGroup]
    total: int


# ==================== TaskLog ====================

class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    level: str
    message: str
    phase: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Article ====================

class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    file_path: str
    publish_date: str
    read_count: int
    like_count: int
    old_like_count: int
    task_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArticleDetailResponse(ArticleResponse):
    content: str = ""  # Markdown 正文

class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int


# ==================== Stats ====================

class StatsOverview(BaseModel):
    total_articles: int = 0
    total_reads: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    running_tasks: int = 0

class DailyStats(BaseModel):
    date: str
    count: int

class TopReadArticle(BaseModel):
    id: int
    title: str
    read_count: int
    publish_date: str


# ==================== Common ====================

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class TestTokenResponse(BaseModel):
    success: bool
    message: str
