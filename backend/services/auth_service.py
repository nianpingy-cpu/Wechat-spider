"""Playwright 扫码登录服务 —— 自动获取 Cookie/Token/appmsg_token"""
import asyncio
import base64
import time
import re
import threading
from playwright.async_api import async_playwright

from backend.database import SessionLocal
from backend.models import Config

# 全局状态：跟踪登录进程
_active_scans = {}  # {scan_id: {"page": ..., "browser": ..., "status": "scanning"|"done"|"error"}}


async def _do_login(scan_id: str, broadcast_fn):
    """Playwright 登录核心逻辑"""
    browser = None
    try:
        _active_scans[scan_id]["status"] = "starting"

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True, args=[
            "--no-sandbox", "--disable-setuid-sandbox",
            "--disable-dev-shm-usage", "--disable-gpu",
        ])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # 打开微信公众平台登录页
        await page.goto("https://mp.weixin.qq.com/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        _active_scans[scan_id]["status"] = "scanning"
        last_url = page.url

        # 轮询：截图发前端，检测登录
        for _ in range(120):  # 最多 4 分钟
            if scan_id not in _active_scans:
                break

            # 截图推给前端
            try:
                screenshot = await page.screenshot(type="png")
                b64 = base64.b64encode(screenshot).decode("utf-8")
                await broadcast_fn({
                    "type": "qrcode",
                    "image": f"data:image/png;base64,{b64}",
                    "scan_id": scan_id,
                })
            except Exception:
                pass

            # 检测 URL 变化（登录成功会跳转）
            current_url = page.url
            if current_url != last_url and "token=" in current_url:
                _active_scans[scan_id]["status"] = "done"

                # 提取 token
                token_match = re.search(r'token=(\d+)', current_url)
                token = token_match.group(1) if token_match else ""

                # 提取 Cookies
                cookies = await context.cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                # 尝试获取 appmsg_token
                appmsg_token = ""
                if cookie_str and token:
                    try:
                        await page.goto(f"https://mp.weixin.qq.com/cgi-bin/appmsg?"
                                        f"action=list_ex&begin=0&count=1&type=9&token={token}"
                                        f"&lang=zh_CN&f=json&ajax=1",
                                        wait_until="networkidle", timeout=15000)
                        await asyncio.sleep(2)
                        # 从请求中拦截 appmsg_token
                        for req in page._requests or []:
                            if "appmsg_token" in (req.url if hasattr(req, 'url') else ""):
                                am = re.search(r'appmsg_token=(\d+)', req.url if hasattr(req, 'url') else "")
                                if am:
                                    appmsg_token = am.group(1)
                                    break
                    except Exception:
                        pass

                # 写入数据库
                try:
                    db = SessionLocal()
                    for key, value in [
                        ("token", token),
                        ("cookie", cookie_str),
                        ("appmsg_token", appmsg_token),
                    ]:
                        cfg = db.query(Config).filter(Config.key == key).first()
                        if cfg:
                            cfg.value = value
                        else:
                            db.add(Config(key=key, value=value))
                    db.commit()
                    db.close()
                except Exception:
                    pass

                await broadcast_fn({
                    "type": "login_success",
                    "scan_id": scan_id,
                    "token": token,
                    "cookie": cookie_str[:50] + "...",
                    "appmsg_token": appmsg_token,
                })
                break

            last_url = current_url
            await asyncio.sleep(2)

        # 超时
        if _active_scans.get(scan_id, {}).get("status") == "scanning":
            await broadcast_fn({
                "type": "login_timeout",
                "scan_id": scan_id,
                "message": "扫码超时，请重试",
            })

    except Exception as e:
        if scan_id in _active_scans:
            _active_scans[scan_id]["status"] = "error"
            try:
                await broadcast_fn({
                    "type": "login_error",
                    "scan_id": scan_id,
                    "message": str(e),
                })
            except Exception:
                pass
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if scan_id in _active_scans:
            del _active_scans[scan_id]


def start_scan_login(scan_id: str, broadcast_fn):
    """在新线程中启动 Playwright 登录"""
    _active_scans[scan_id] = {"status": "initializing"}

    def _run():
        asyncio.run(_do_login(scan_id, broadcast_fn))

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def cancel_scan(scan_id: str):
    """取消扫码"""
    if scan_id in _active_scans:
        del _active_scans[scan_id]
