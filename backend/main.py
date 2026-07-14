"""FastAPI 应用入口"""
import os
import sys

# 确保项目根目录在 sys.path 中，以便导入原始脚本
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.config import CORS_ORIGINS
from backend.routers import config_router, task_router, article_router, stats_router

app = FastAPI(title="WeChat Spider API", version="1.0.0", docs_url="/docs")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(config_router.router, prefix="/api", tags=["Config"])
app.include_router(task_router.router, prefix="/api", tags=["Tasks"])
app.include_router(article_router.router, prefix="/api", tags=["Articles"])
app.include_router(stats_router.router, prefix="/api", tags=["Stats"])


@app.on_event("startup")
def on_startup():
    init_db()
    os.makedirs(os.path.join(BASE_DIR, "police_country_articles"), exist_ok=True)


@app.get("/")
def root():
    return {"message": "WeChat Spider API is running", "docs": "/docs"}
