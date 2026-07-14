"""SQLAlchemy 数据模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(32), nullable=False, comment="fetch_urls | crawl_articles")
    status = Column(String(16), default="pending", index=True,
                    comment="pending | running | paused | completed | failed")
    input_file = Column(String(256), default="")
    start_page = Column(Integer, default=1)
    end_page = Column(Integer, default=1)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    parent_task_id = Column(Integer, ForeignKey("task.id"), nullable=True, comment="父任务 ID（用于子任务串联）")
    batch_id = Column(String(64), default="", index=True, comment="批次 ID（同一批次任务共享）")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class TaskLog(Base):
    __tablename__ = "task_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(16), default="info", comment="info | success | warning | error")
    message = Column(Text, default="")
    phase = Column(String(32), default="", comment="searching | fetching | crawling | stats | retry | pipeline")
    created_at = Column(DateTime, default=datetime.utcnow)


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), default="无标题")
    url = Column(String(512), unique=True, nullable=False)
    file_path = Column(String(512), default="")
    publish_date = Column(String(32), default="")
    read_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    old_like_count = Column(Integer, default=0)
    task_id = Column(Integer, ForeignKey("task.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), default="")
    role = Column(String(16), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)
