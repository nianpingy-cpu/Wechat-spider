"""封装原有 crawler_core.py 的文章爬取逻辑"""
import sys
import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
import html2text
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database import SessionLocal
from backend.models import Task, TaskLog, Article
from backend.ws_manager import manager


def add_log(task_id: int, level: str, message: str):
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


def crawl_articles(task_id: int, cookie: str, appmsg_token: str,
                   input_file: str, output_dir: str = "police_country_articles"):
    """后台线程：爬取文章内容和统计数据"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        task.status = "running"
        db.commit()

        # 读取 URL 列表
        filepath = os.path.join(BASE_DIR, input_file)
        if not os.path.exists(filepath):
            add_log(task_id, "error", f"❌ 文件不存在: {input_file}")
            task.status = "failed"
            db.commit()
            return

        with open(filepath, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        task.total_count = len(urls)
        db.commit()
        add_log(task_id, "info", f"🎯 读取到 {len(urls)} 个任务，开始执行...")

        # 初始化 html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.bypass_tables = False
        h.ignore_images = True

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
            "Origin": "https://mp.weixin.qq.com",
            "Referer": "https://mp.weixin.qq.com/",
        }

        os.makedirs(os.path.join(BASE_DIR, output_dir), exist_ok=True)

        success = 0
        fail = 0
        wrong_urls = []

        for idx, url in enumerate(urls):
            db.refresh(task)
            if task.status == "paused":
                add_log(task_id, "warning", "⏸️ 任务已暂停")
                # 保存剩余 URL 供断点续传
                remaining_file = os.path.join(BASE_DIR, "remaining_urls.txt")
                with open(remaining_file, "w", encoding="utf-8") as rf:
                    for u in urls[idx:]:
                        rf.write(u + "\n")
                add_log(task_id, "info", f"💾 剩余 {len(urls) - idx} 个 URL 已保存至 remaining_urls.txt")
                db.close()
                return

            try:
                add_log(task_id, "info", f"🚀 [{idx+1}/{len(urls)}] 开始处理: {url[:80]}...")

                # 获取正文
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    raise Exception(f"HTTP 状态码错误: {response.status_code}")

                response.encoding = "utf-8"
                html_text = response.text
                soup = BeautifulSoup(html_text, "html.parser")

                # 提取标题
                title_node = soup.find("h1", {"id": "activity-name"})
                title = title_node.get_text().strip() if title_node else "无标题"
                safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]

                # 提取发布时间
                ct_match = re.search(r'var ct = "(\d+)"', html_text)
                if ct_match:
                    ts = int(ct_match.group(1))
                    date_str = datetime.fromtimestamp(ts).strftime("%Y年%m月%d日")
                else:
                    date_str = datetime.now().strftime("%Y年%m月%d日")

                # 尝试获取阅读量
                url_params = {}
                for key in ["__biz", "mid", "idx", "sn"]:
                    match = re.search(f'{key}=([^&]+)', url)
                    if match:
                        url_params[key] = match.group(1)

                stats = None
                stats_text = ""
                if cookie and appmsg_token and url_params:
                    try:
                        api_url = "https://mp.weixin.qq.com/mp/getappmsgext"
                        api_params = {
                            "f": "json", "mock": "", "r": random.random(),
                            "uin": "777", "key": "777", "pass_ticket": "",
                            "wxtoken": "777", "devicetype": "Windows-10",
                            "clientversion": "62090529",
                            "__biz": url_params.get("__biz"),
                            "appmsg_token": appmsg_token, "x5": "0"
                        }
                        api_data = {"is_only_read": "1", "is_temp_url": "0",
                                    "appmsg_type": "9", "reward_uin_count": "0"}
                        stats_headers = headers.copy()
                        stats_headers.update({
                            "Cookie": cookie,
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        })
                        resp = requests.post(api_url, params=api_params, data=api_data,
                                             headers=stats_headers, timeout=5)
                        res_json = resp.json()
                        if res_json.get("appmsgstat"):
                            stat = res_json["appmsgstat"]
                            stats = {
                                "read_num": stat.get("read_num", 0),
                                "like_num": stat.get("like_num", 0),
                                "old_like_num": stat.get("old_like_num", 0),
                            }
                    except Exception:
                        pass

                read_num = stats["read_num"] if stats else 0
                like_num = stats["like_num"] if stats else 0
                old_like = stats["old_like_num"] if stats else 0

                if stats:
                    stats_text = f"阅读量: {read_num}  点赞数: {like_num}  在看数: {old_like}\n\n"
                    add_log(task_id, "success", f"📊 阅读: {read_num} | 点赞: {like_num}")

                # 正文处理
                content_div = soup.find("div", {"id": "js_content"})
                if not content_div:
                    if "验证" in soup.get_text():
                        raise Exception("触发验证码/风控")
                    add_log(task_id, "warning", f"❌ 未找到文章内容: {title}")
                    fail += 1
                    wrong_urls.append(url)
                    continue

                # 移除干扰项
                for img in content_div.find_all("img"):
                    img.decompose()
                for qr in content_div.find_all("p", style=re.compile(r"text-align:\s*center")):
                    if qr.find("img"):
                        qr.decompose()

                html_content = str(content_div)
                markdown_content = h.handle(html_content)

                final_content = f"# {title}\n\n发布时间: {date_str}\n\n{stats_text}---\n\n{markdown_content}"

                # 保存 Markdown 文件
                article_filename = f"{safe_title}.md"
                article_path = os.path.join(BASE_DIR, output_dir, article_filename)
                with open(article_path, "w", encoding="utf-8") as af:
                    af.write(final_content)

                # 保存文章元数据到数据库
                existing = db.query(Article).filter(Article.url == url).first()
                if not existing:
                    article = Article(
                        title=title,
                        url=url,
                        file_path=article_path,
                        publish_date=date_str,
                        read_count=read_num,
                        like_count=like_num,
                        old_like_count=old_like,
                        task_id=task_id,
                    )
                    db.add(article)
                else:
                    existing.title = title
                    existing.read_count = read_num
                    existing.like_count = like_num
                    existing.old_like_count = old_like

                db.commit()
                success += 1
                task.success_count = success
                task.fail_count = fail
                db.commit()

                add_log(task_id, "success", f"✅ [{idx+1}/{len(urls)}] 保存成功: {title}")

            except Exception as e:
                add_log(task_id, "error", f"❌ [{idx+1}/{len(urls)}] 处理出错: {e}")
                fail += 1
                wrong_urls.append(url)
                task.fail_count = fail
                db.commit()

                # 写入错误文件
                wrong_file = os.path.join(BASE_DIR, "url_wrong.txt")
                with open(wrong_file, "a", encoding="utf-8") as wf:
                    wf.write(url + "\n")

            # 随机延时
            time.sleep(random.uniform(2, 5))

        task.status = "completed"
        task.finished_at = datetime.utcnow()
        db.commit()
        add_log(task_id, "success",
                f"🏁 全部完成！成功: {success}, 失败: {fail}, 失败链接已保存至 url_wrong.txt")

    except Exception as e:
        add_log(task_id, "error", f"💥 严重错误: {e}")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            db.commit()
    finally:
        db.close()
