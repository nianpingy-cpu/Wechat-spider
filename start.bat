@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════╗
echo ║     🕵️  WeChat Spider 管理系统 一键启动      ║
echo ╚══════════════════════════════════════════════╝
echo.

echo [1/2] 启动后端服务 (FastAPI)...
start "WeChat Spider Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo   ✅ 后端已启动，访问 http://localhost:8000/docs 查看 API 文档

echo [2/2] 启动前端服务 (Vite)...
start "WeChat Spider Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo   ✅ 前端已启动，访问 http://localhost:5173 打开管理界面

echo.
echo ═══════════════════════════════════════════════
echo   🎉 全部启动完成！
echo   前端地址: http://localhost:5173
echo   API 文档: http://localhost:8000/docs
echo ═══════════════════════════════════════════════
echo.
echo 按任意键退出此窗口（不会关闭前后端服务）
pause >nul
