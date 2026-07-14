#!/bin/bash
echo "🕵️  WeChat Spider 管理系统 一键启动"
echo ""

# 安装依赖（如果没有）
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 正在安装前端依赖..."
    cd frontend && npm install && cd ..
fi

echo "[1/2] 启动后端服务 (FastAPI)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  ✅ 后端已启动 (PID: $BACKEND_PID)"

echo "[2/2] 启动前端服务 (Vite)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
echo "  ✅ 前端已启动 (PID: $FRONTEND_PID)"

echo ""
echo "═══════════════════════════════════"
echo "  🎉 全部启动完成！"
echo "  前端地址: http://localhost:5173"
echo "  API 文档: http://localhost:8000/docs"
echo "═══════════════════════════════════"
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
