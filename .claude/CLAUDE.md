# GTCS 全球贸易通关系统 — 项目说明

## 启动方式

后端（backend 目录）：
```
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端（frontend 目录）：
```
cd frontend && npm run dev   # 开发模式 :5173
cd frontend && npm run build # 构建到 backend/static/
```

数据库：`backend/data/gtcs.db`（SQLite，ORM 自动建表）

## 技术栈

- **后端**: Python 3.9+ / FastAPI / SQLAlchemy 2.0 同步 / SQLite
- **前端**: Vue 3 + Element Plus + Vite
- **认证**: JWT + bcrypt，全局 auth middleware
- **搜索**: SQLite FTS5（tariff_fts 索引 16 万条, screening_fts 235 条）

## 架构要点

- `app/api/v1/` — 路由，每个文件一个模块
- `app/services/` — 业务逻辑（tariff_service, cost_service, enterprise_cost_simulator 等）
- `app/models/` — SQLAlchemy ORM 模型
- `app/core/` — 配置、数据库、安全
- `app/schemas/` — Pydantic 请求/响应模型
- `app/main.py` — 应用入口，lifespan 中 seed 预裁定和审计日志
- `scripts/` — 工具脚本（tariff 数据导入等）

## 核心功能模块

| 路由前缀 | 功能 |
|-----------|------|
| /api/v1/tariff | 税则查询/浏览/搜索 |
| /api/v1/fta | FTA 优惠推荐/比较 |
| /api/v1/cost | 成本模拟（含企业版） |
| /api/v1/hs-classification | HS 归类工作台 |
| /api/v1/origin | 原产地判定 |
| /api/v1/declaration | 报关单管理 |
| /api/v1/screening | 制裁名单筛查 |
| /api/v1/price-risk | 价格风险监控 |
| /api/v1/enterprise | 企业管理 |
| /api/v1/product | 产品管理 |
| /api/v1/audit | 审计日志 |
| /api/v1/dashboard | 仪表盘统计 |

## 预裁定数据

共 9 条 seed 预裁定（COUNTRY: hs_code）：
- CN: 85285200 交互式智能平板, 84714190 工控机, 85176299 5G CPE
- US: 85285900 Interactive Flat Panel, 84713001 Tablet
- DE: 85284900 激光投影, 85414300 光伏板
- VN: 85285900 LCD 显示器
- JP: 85258900 工业相机

## 已知限制

- 中国（CN）的 NationalTariffLine 为 0 条（tariff 数据只导入了其他 11 个国家）
- 预算定 search 在 HS code 前 6 位截断匹配
