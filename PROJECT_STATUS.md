# WeChat Spider 项目状态存档

> 最后更新：2026-07-14  
> GitHub：https://github.com/nianpingy-cpu/Wechat-spider  
> 分支：`web-dashboard`

---

## 一、项目概览

微信公众号文章采集 Web 管理系统，全栈项目。

| 层级 | 技术栈 | 入口 |
|------|--------|------|
| 前端 | Vue 3 + Vite + Element Plus | `frontend/` |
| 后端 | FastAPI + SQLite + WebSocket | `backend/` |
| 爬虫核心 | Python (requests/BS4/html2text) | `crawler_core.py`, `get_urls_api.py`, `resume_helper.py` |

---

## 二、线上部署

| 组件 | 地址 | 平台 |
|------|------|------|
| 🖥️ 前端 | `https://wechat-spider.vercel.app` | Vercel |
| ☁️ API 代理 | `https://wechat-spider-api.wechat-spider.workers.dev` | Cloudflare Workers |
| 🏠 后端 | `https://wechat-spider.onrender.com` | Render |

### 环境变量

前端 `frontend/.env.production`：
```
VITE_API_BASE_URL=https://wechat-spider-api.wechat-spider.workers.dev
VITE_WS_URL=https://wechat-spider.onrender.com
```

- HTTP 请求走 Cloudflare Worker 代理（避免 Render 休眠超时）
- WebSocket 直连 Render（Worker 不支持 WebSocket 透传）

---

## 三、已完成的模块 ✅

### 1. 前端页面（5 页 + 布局）

```
/           Dashboard   仪表盘：统计卡片 + 运行中任务 + 快捷操作
/config     Config      配置管理：手动填写 + 扫码登录入口
/tasks      Tasks       任务管理：创建/启动/暂停 + 实时日志终端
/articles   Articles    文章浏览：搜索/分页/预览 Markdown/导出 CSV+JSON
/stats      Stats       统计看板：ECharts 图表 + 阅读量排行榜
```

关键组件：
- `LogTerminal.vue` — WebSocket 实时日志终端 + phase 筛选标签
- `TaskCreateDialog.vue` — 创建任务弹窗（4 种任务类型）
- `QrcodeLogin.vue` — 扫码登录弹窗
- `ArticlePreview.vue` — Markdown 文章预览
- `TaskProgressCard.vue` — 任务进度卡片

### 2. 后端 API

| 路由文件 | 端点 | 功能 |
|----------|------|------|
| `config_router.py` | `/api/config` | 配置 CRUD + 测试连接 |
| `config_router.py` | `/api/ws/qrcode/{scan_id}` | **WebSocket** 扫码 QR 推送 |
| `task_router.py` | `/api/tasks` | 任务 CRUD + 启动/暂停/重试 |
| `task_router.py` | `/api/ws/tasks/{task_id}` | **WebSocket** 任务实时日志 |
| `task_router.py` | `/api/tasks/batches` | 批次列表 |
| `task_router.py` | `/api/tasks/batch/{batch_id}` | 批次子任务 |
| `article_router.py` | `/api/articles` | 文章列表/搜索/详情/删除/导出 |
| `stats_router.py` | `/api/stats/overview` | 总览统计 |
| `stats_router.py` | `/api/stats/daily` | 每日文章数 |
| `stats_router.py` | `/api/stats/top-read` | 阅读量 Top 10 |

### 3. 数据库模型（SQLite）

```
Config    — key/value 配置（token, cookie, appmsg_token, target_name）
Task      — 爬虫任务（4 种类型 + 状态/进度/batch_id/parent_task_id）
TaskLog   — 任务日志（level + message + phase 阶段标签）
Article   — 文章元数据（title, url, read_count, like_count, old_like_count）
User      — 用户（预留，未使用）
```

Phase 标签值：`searching` | `fetching` | `crawling` | `stats` | `retry` | `pipeline`

### 4. 服务层

| 文件 | 功能 |
|------|------|
| `log_service.py` | 统一日志（写 DB + WebSocket 广播 + 进度更新） |
| `url_fetcher_service.py` | 抓取公众号文章链接列表 |
| `crawler_service.py` | 爬取文章正文到 Markdown |
| `stats_service.py` | 独立更新阅读量/点赞/在看 |
| `pipeline_service.py` | 全流程编排（fetch_urls → crawl_content → fetch_stats） |
| `auth_service.py` | Playwright 扫码登录 |
| `resume_service.py` | 断点续传（生成剩余 URL 列表） |

### 5. 任务类型（4 种）

| type | 功能 | 依赖配置 |
|------|------|---------|
| `fetch_urls` | 抓取链接 | Token + Cookie + 公众号名称 |
| `crawl_content` | 爬取正文（不抓阅读量） | Cookie |
| `fetch_stats` | 更新阅读量/点赞/在看 | Cookie + AppMsg Token |
| `full_pipeline` | 一键全流程（1→2→3 自动串联） | Token + Cookie |

### 6. 部署配置

| 文件 | 用途 |
|------|------|
| `render.yaml` | Render Web Service（含 playwright install chromium） |
| `vercel.json` | Vercel 前端部署 |
| `cf-worker/wrangler.toml` | Cloudflare Worker API 代理 |
| `Dockerfile` | Fly.io 备用 |
| `fly.toml` | Fly.io 备用 |
| `start.bat` / `start.sh` | 本地一键启动 |

---

## 四、未完成 / 有问题的模块 ❌

### 1. P2 扫码登录（代码已写，Render 未部署成功）

**状态**：代码已完成并推送，但 **Render 尚未重新部署**，WebSocket 返回 404。

**原因**：本地测试 WebSocket 路由正常，但 Render 上所有 WebSocket 端点都返回 404，说明 Render 拉取的是旧代码（最后一次 deploy 在 P0/P1 之后）。

**解决**：去 Render 控制台 → Manual Deploy → Deploy latest commit → 等待构建完成。如果 Playwright Chromium（~400MB）构建失败，需要换成轻量方案。

**涉及文件**：
- `backend/services/auth_service.py`
- `backend/routers/config_router.py`（WebSocket 端点和 REST 端点）
- `frontend/src/components/config/QrcodeLogin.vue`
- `frontend/src/views/Config.vue`

### 2. Cloudflare Tunnel（放弃）

**原因**：QUIC/HTTP2 协议在国内被墙，`cloudflared tunnel` 无法连接 Cloudflare 边缘节点。

### 3. Fly.io（放弃）

**原因**：需要海外信用卡。

### 4. 用户认证系统（未实现）

User 表已创建，但没有登录/注册 API，前端也不需要登录。

---

## 五、已知 bugs / 注意事项

1. **Render 15 分钟休眠**：免费实例无请求 15 分钟自动休眠，首次唤醒需 30-60 秒。Worker 有重试机制缓解。
2. **Worker 不支持 WebSocket 透传**：WebSocket 直连 Render（VITE_WS_URL），不走 Worker。
3. **AppMsg Token 有效期短**：约 10 分钟，过期后阅读量抓取失败但不影响正文爬取。
4. **统计抓取静默失败**：`crawler_service.py` 中 stats API 调用失败时 `except: pass`，用户无感知。
5. **任务暂停是协作式的**：线程轮询 DB 的 `task.status`，非强制终止。sleep 被拆分为 1 秒片段以响应暂停。
6. **数据库是本地文件**：`wechat_spider.db` 在 Render 上是临时的，每次重新部署会被重置。

---

## 六、本地开发

```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 启动后端（终端 1）
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（终端 2）
cd frontend && npm run dev

# 访问
# 前端: http://localhost:5173
# API 文档: http://localhost:8000/docs
```

---

## 七、后续建议

| 优先级 | 任务 |
|--------|------|
| 🔴 高 | 让 Render 重新部署，确认 WebSocket + 扫码登录正常工作 |
| 🔴 高 | 如果 Playwright 太大，换轻量扫码方案（直接请求 QR 图片 + 轮询） |
| 🟡 中 | 增加 UptimeRobot 保活（14 分钟 ping 一次 Render） |
| 🟡 中 | `crawler_service.py` stats 失败时增加日志警告 |
| 🟢 低 | 用户认证系统（多用户支持） |
| 🟢 低 | 移动端适配 |
| 🟢 低 | 文章全文搜索（ES/FTS5） |

---

## 八、发给新对话时需要的上下文

> 项目根目录：`C:\Users\27796\wechat-spider-repo`  
> 当前分支：`web-dashboard`  
> 前端在线：https://wechat-spider.vercel.app  
> 后端在线：https://wechat-spider.onrender.com  
> Worker 在线：https://wechat-spider-api.wechat-spider.workers.dev  
> **扫码登录代码已写但 WebSocket 404，需要让 Render 部署最新 commit**
