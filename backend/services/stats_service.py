"""独立统计抓取服务 —— 单独更新文章阅读量/点赞/在看"""
import sys
import os
import re
import time
import random
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database import SessionLocal
from backend.models import Task, Article
from backend.services.log_service import add_log, update_task_progress


def fetch_stats(task_id: int, cookie: str, appmsg_token: str,
                article_ids: list = None):
    """后台线程：从 Article 表读取 URL，调 stats API 更新阅读量/点赞/在看"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        task.status = "running"
        db.commit()

        add_log(task_id, "info", "📊 开始抓取统计数据...", "stats")

        # 查询文章列表
        q = db.query(Article)
        if article_ids:
            q = q.filter(Article.id.in_(article_ids))
        articles = q.all()

        task.total_count = len(articles)
        db.commit()
        add_log(task_id, "info", f"📋 共 {len(articles)} 篇文章需要更新统计数据", "stats")

        if len(articles) == 0:
            add_log(task_id, "warning", "⚠️ 没有找到需要统计的文章", "stats")
            task.status = "completed"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
            "Origin": "https://mp.weixin.qq.com",
            "Referer": "https://mp.weixin.qq.com/",
            "Cookie": cookie,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        success = 0
        fail = 0

        for idx, article in enumerate(articles):
            db.refresh(task)
            if task.status == "paused":
                add_log(task_id, "warning", "⏸️ 统计任务已暂停", "stats")
                db.close()
                return

            try:
                # 从 URL 提取参数
                url_params = {}
                for key in ["__biz", "mid", "idx", "sn"]:
                    match = re.search(f'{key}=([^&]+)', article.url)
                    if match:
                        url_params[key] = match.group(1)

                if not url_params.get("__biz"):
                    add_log(task_id, "warning",
                            f"⚠️ [{idx+1}/{len(articles)}] 无法解析 URL: {article.title[:30]}", "stats")
                    fail += 1
                    continue

                # 调用 stats API
                api_url = "https://mp.weixin.qq.com/mp/getappmsgext"
                params = {
                    "f": "json", "mock": "", "r": random.random(),
                    "uin": "777", "key": "777", "pass_ticket": "",
                    "wxtoken": "777", "devicetype": "Windows-10",
                    "clientversion": "62090529",
                    "__biz": url_params.get("__biz"),
                    "appmsg_token": appmsg_token, "x5": "0"
                }
                body = {"is_only_read": "1", "is_temp_url": "0",
                        "appmsg_type": "9", "reward_uin_count": "0"}

                resp = requests.post(api_url, params=params, data=body,
                                     headers=headers, timeout=8)
                res_json = resp.json()

                if res_json.get("appmsgstat"):
                    stat = res_json["appmsgstat"]
                    article.read_count = stat.get("read_num", 0) or 0
                    article.like_count = stat.get("like_num", 0) or 0
                    article.old_like_count = stat.get("old_like_num", 0) or 0
                    db.commit()

                    success += 1
                    add_log(task_id, "success",
                            f"📊 [{idx+1}/{len(articles)}] {article.title[:25]}... "
                            f"阅读:{article.read_count} 点赞:{article.like_count} 在看:{article.old_like_count}",
                            "stats")

                    update_task_progress(task_id, success_count=success,
                                         fail_count=fail, total_count=len(articles))
                else:
                    fail += 1
                    add_log(task_id, "warning",
                            f"⚠️ [{idx+1}/{len(articles)}] 无统计数据: {article.title[:30]}",
                            "stats")

                # 延时防封
                time.sleep(random.uniform(1.5, 4))

            except Exception as e:
                fail += 1
                add_log(task_id, "error",
                        f"❌ [{idx+1}/{len(articles)}] 统计抓取失败: {e}", "stats")

        task.status = "completed"
        task.finished_at = datetime.utcnow()
        task.success_count = success
        task.fail_count = fail
        db.commit()
        add_log(task_id, "success",
                f"🏁 统计更新完成！成功: {success}, 失败: {fail}", "stats")

    except Exception as e:
        add_log(task_id, "error", f"💥 统计任务严重错误: {e}", "stats")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            db.commit()
    finally:
        db.close()
