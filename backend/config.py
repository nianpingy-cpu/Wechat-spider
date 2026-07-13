"""后端配置读取"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 文章输出目录
OUTPUT_DIR = os.path.join(BASE_DIR, "police_country_articles")

# CORS 允许的前端地址
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
