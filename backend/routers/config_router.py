"""配置管理 API"""
import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Config
from backend.schemas import ConfigItem, ConfigUpdateRequest, ConfigResponse, MessageResponse, TestTokenResponse

router = APIRouter()


@router.get("/config", response_model=list[ConfigResponse])
def get_configs(db: Session = Depends(get_db)):
    """获取所有配置项"""
    configs = db.query(Config).all()
    result = []
    # 默认配置项
    default_keys = {"token": "", "cookie": "", "appmsg_token": "", "target_name": ""}
    existing_keys = {c.key: c for c in configs}

    for key, default_value in default_keys.items():
        if key in existing_keys:
            result.append(existing_keys[key])
        else:
            # 自动创建默认配置项
            cfg = Config(key=key, value=default_value)
            db.add(cfg)
            db.commit()
            db.refresh(cfg)
            result.append(cfg)

    return result


@router.put("/config", response_model=MessageResponse)
def update_config(req: ConfigUpdateRequest, db: Session = Depends(get_db)):
    """批量更新配置项"""
    for item in req.items:
        cfg = db.query(Config).filter(Config.key == item.key).first()
        if cfg:
            cfg.value = item.value
        else:
            cfg = Config(key=item.key, value=item.value)
            db.add(cfg)
    db.commit()
    return MessageResponse(message="配置已更新")


@router.post("/config/test-token", response_model=TestTokenResponse)
def test_token(db: Session = Depends(get_db)):
    """测试 Token 和 Cookie 是否有效"""
    token_cfg = db.query(Config).filter(Config.key == "token").first()
    cookie_cfg = db.query(Config).filter(Config.key == "cookie").first()
    target_cfg = db.query(Config).filter(Config.key == "target_name").first()

    token = token_cfg.value if token_cfg else ""
    cookie = cookie_cfg.value if cookie_cfg else ""
    target_name = target_cfg.value if target_cfg else ""

    if not token or not cookie:
        return TestTokenResponse(success=False, message="Token 或 Cookie 未配置")

    try:
        url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        params = {
            "action": "search_biz", "begin": "0", "count": "5",
            "query": target_name or "测试", "token": token,
            "lang": "zh_CN", "f": "json", "ajax": "1"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
            "Cookie": cookie
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()

        if "base_resp" in data and data["base_resp"]["ret"] == 200003:
            return TestTokenResponse(success=False, message="Token 或 Cookie 已失效，请重新获取")

        list_count = len(data.get("list", []))
        return TestTokenResponse(
            success=True,
            message=f"连接成功！搜索到 {list_count} 个相关公众号"
        )
    except Exception as e:
        return TestTokenResponse(success=False, message=f"连接失败: {str(e)}")
