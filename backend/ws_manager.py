"""WebSocket 连接管理器 —— 推送实时日志到前端"""
import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # task_id → [WebSocket, ...]
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, task_id: int, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, task_id: int, websocket: WebSocket):
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def broadcast(self, task_id: int, data: dict):
        """向监听某个任务的所有 WebSocket 客户端广播消息"""
        if task_id not in self.active_connections:
            return
        message = json.dumps(data, ensure_ascii=False)
        dead = []
        for ws in self.active_connections[task_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)

    def broadcast_sync(self, task_id: int, data: dict):
        """同步版本的广播（供后台线程使用）"""
        if task_id not in self.active_connections:
            return
        message = json.dumps(data, ensure_ascii=False)
        dead = []
        for ws in self.active_connections[task_id]:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(ws.send_text(message), loop)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)


manager = ConnectionManager()
