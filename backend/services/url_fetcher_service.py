"""封装原有 get_urls_api.py 的链接抓取逻辑"""
import sys
import os
import requests
import time
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database import SessionLocal
from backend.models import Task, TaskLog
from backend.ws_manager import manager


def add_log(task_id: int, level: str, message: str):
    """写入日志到数据库并广播 WebSocket"""
    db = SessionLocal()
    try:
        log = TaskLog(task_id=task_id, level=level, message=message)
        db.add(log)
        db.commit()
    finally:
        db.close()
    manager.broadcast_sync(task_id, {
        "type": "log",
        "task_id": task_id,
        "level": level,
        "message": message,
        "time": datetime.utcnow().strftime("%H:%M:%S")
    })


def fetch_urls(task_id: int, token: str, cookie: str, target_name: str,
               start_page: int, end_page: int, output_file: str):
    """后台线程：抓取公众号文章链接"""
    db = SessionLocal()
    try:
        # 更新任务状态
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        task.status = "running"
        task.start_page = start_page
        task.end_page = end_page
        task.input_file = output_file
        db.commit()

        add_log(task_id, "info", f"🔍 正在搜索公众号: {target_name} ...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
            "Cookie": cookie
        }

        # Step 1: 获取 fakeid
        search_url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        params = {
            "action": "search_biz", "begin": "0", "count": "5",
            "query": target_name, "token": token, "lang": "zh_CN",
            "f": "json", "ajax": "1"
        }
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = resp.json()

        if "base_resp" in data and data["base_resp"]["ret"] == 200003:
            add_log(task_id, "error", "❌ Token 或 Cookie 已失效！")
            task.status = "failed"
            db.commit()
            return

        fakeid = None
        for item in data.get("list", []):
            if item["nickname"] == target_name:
                fakeid = item["fakeid"]
                add_log(task_id, "success", f"✅ 找到目标! FakeID: {fakeid}")
                break

        if not fakeid:
            add_log(task_id, "error", "❌ 未找到该公众号，请检查名称是否正确。")
            task.status = "failed"
            db.commit()
            return

        # Step 2: 抓取链接
        appmsg_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        filepath = os.path.join(BASE_DIR, output_file)

        total_linked = 0
        with open(filepath, "a", encoding="utf-8") as f:
            for i in range(start_page, end_page):
                # 检查是否被暂停
                db.refresh(task)
                if task.status == "paused":
                    add_log(task_id, "warning", "⏸️ 任务已暂停")
                    db.close()
                    return

                add_log(task_id, "info", f"📄 [进度] 正在抓取第 {i} 页 (begin={i*5})...")

                params = {
                    "token": token, "lang": "zh_CN", "f": "json", "ajax": "1",
                    "action": "list_ex", "begin": str(i * 5), "count": "5",
                    "query": "", "fakeid": fakeid, "type": "9",
                }

                try:
                    resp = requests.get(appmsg_url, params=params, headers=headers, timeout=15)
                    data = resp.json()

                    ret_code = data.get("base_resp", {}).get("ret")
                    if ret_code == 200013:
                        add_log(task_id, "error", "🛑 触发微信频率限制 (Ret 200013)！请等待 1-4 小时后再试。")
                        task.status = "failed"
                        db.commit()
                        break

                    if ret_code == 200003:
                        add_log(task_id, "error", "❌ Cookie/Token 已过期，请重新获取。")
                        task.status = "failed"
                        db.commit()
                        break

                    msg_list = data.get("app_msg_list")
                    if not msg_list:
                        add_log(task_id, "success", "✅ 已无更多文章，采集结束。")
                        break

                    for item in msg_list:
                        link = item["link"]
                        title = item["title"]
                        f.write(link + "\n")
                        total_linked += 1
                        add_log(task_id, "info", f"   - {title}")

                    task.total_count = total_linked
                    task.success_count = total_linked
                    db.commit()

                    # 防封延时
                    if i > start_page and i % 5 == 0:
                        long_sleep = random.randint(30, 60)
                        add_log(task_id, "info", f"☕ 抓取了 5 页，休息 {long_sleep} 秒防风控...")
                        # 分段 sleep 以便响应暂停
                        for _ in range(long_sleep):
                            time.sleep(1)
                            db.refresh(task)
                            if task.status == "paused":
                                add_log(task_id, "warning", "⏸️ 任务已暂停")
                                db.close()
                                return
                    else:
                        short_sleep = random.randint(10, 15)
                        add_log(task_id, "info", f"⏳ 等待 {short_sleep} 秒...")
                        for _ in range(short_sleep):
                            time.sleep(1)
                            db.refresh(task)
                            if task.status == "paused":
                                add_log(task_id, "warning", "⏸️ 任务已暂停")
                                db.close()
                                return

                except Exception as e:
                    add_log(task_id, "error", f"❌ 请求页码 {i} 失败: {e}")
                    time.sleep(20)
                    continue

        task.status = "completed"
        task.finished_at = datetime.utcnow()
        db.commit()
        add_log(task_id, "success", f"🎉 采集结束！共 {total_linked} 条链接，已保存至 {output_file}")

    except Exception as e:
        add_log(task_id, "error", f"💥 严重错误: {e}")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            db.commit()
    finally:
        db.close()
