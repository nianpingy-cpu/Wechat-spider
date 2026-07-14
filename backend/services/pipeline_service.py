"""全流程编排服务 —— 自动串联 fetch_urls → crawl_content → fetch_stats"""
import uuid
import threading
from backend.database import SessionLocal
from backend.models import Task


def run_full_pipeline(db_task_id: int, config: dict):
    """
    全流程一键执行：
    1. 创建子任务 fetch_urls
    2. 完成后自动创建 crawl_content
    3. 完成后自动创建 fetch_stats
    """
    batch_id = uuid.uuid4().hex[:12]
    db = SessionLocal()

    try:
        parent = db.query(Task).filter(Task.id == db_task_id).first()
        if not parent:
            return

        token = config.get("token", "")
        cookie = config.get("cookie", "")
        appmsg_token = config.get("appmsg_token", "")
        target_name = config.get("target_name", "")
        start_page = parent.start_page or 1
        end_page = parent.end_page or 50

        # === Phase 1: fetch_urls ===
        output_file = f"url_({start_page}-{end_page})_{batch_id}.txt"

        sub1 = Task(type="fetch_urls", status="pending",
                    start_page=start_page, end_page=end_page,
                    input_file=output_file,
                    parent_task_id=parent.id, batch_id=batch_id)
        db.add(sub1)
        db.commit()
        db.refresh(sub1)

        parent.batch_id = batch_id
        db.commit()

        from backend.services.url_fetcher_service import fetch_urls
        from backend.services.log_service import add_log

        add_log(sub1.id, "info", f"🔄 [全流程 Phase 1/3] 开始抓取链接 (任务 #{sub1.id})", "pipeline")

        t1 = threading.Thread(target=fetch_urls,
                              args=(sub1.id, token, cookie, target_name,
                                    start_page, end_page, output_file),
                              daemon=True)
        t1.start()
        t1.join()  # 等待 Phase 1 完成

        db.refresh(sub1)
        if sub1.status != "completed":
            add_log(parent.id, "error", f"❌ Phase 1 失败，全流程终止", "pipeline")
            parent.status = "failed"
            db.commit()
            return

        # === Phase 2: crawl_content ===
        sub2 = Task(type="crawl_content", status="pending",
                    input_file=output_file,
                    parent_task_id=parent.id, batch_id=batch_id)
        db.add(sub2)
        db.commit()
        db.refresh(sub2)

        add_log(sub2.id, "info", f"🔄 [全流程 Phase 2/3] 开始爬取正文 (任务 #{sub2.id})", "pipeline")

        from backend.services.crawler_service import crawl_articles

        t2 = threading.Thread(target=crawl_articles,
                              args=(sub2.id, cookie, appmsg_token, output_file),
                              daemon=True)
        t2.start()
        t2.join()

        db.refresh(sub2)
        if sub2.status != "completed":
            add_log(parent.id, "error", f"❌ Phase 2 失败，全流程终止", "pipeline")
            parent.status = "failed"
            db.commit()
            return

        # === Phase 3: fetch_stats ===
        sub3 = Task(type="fetch_stats", status="pending",
                    parent_task_id=parent.id, batch_id=batch_id)
        db.add(sub3)
        db.commit()
        db.refresh(sub3)

        add_log(sub3.id, "info", f"🔄 [全流程 Phase 3/3] 开始抓取阅读量 (任务 #{sub3.id})", "pipeline")

        from backend.services.stats_service import fetch_stats

        t3 = threading.Thread(target=fetch_stats,
                              args=(sub3.id, cookie, appmsg_token),
                              daemon=True)
        t3.start()
        t3.join()

        parent.status = "completed"
        db.commit()
        add_log(parent.id, "success", f"🎉 全流程完成！ 批次: {batch_id}", "pipeline")

    except Exception as e:
        from backend.services.log_service import add_log
        add_log(db_task_id, "error", f"💥 全流程严重错误: {e}", "pipeline")
        try:
            parent = db.query(Task).filter(Task.id == db_task_id).first()
            if parent:
                parent.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
