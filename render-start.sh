#!/bin/bash
# Render 启动脚本
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
