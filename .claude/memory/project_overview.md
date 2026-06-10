---
name: GTCS 项目概览
description: 全球贸易通关系统的架构、技术栈、启动方式和核心模块
type: project
---

# GTCS 全球贸易通关系统

## 目录结构
```
GTCS/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/   # 路由
│   │   ├── services/ # 业务逻辑
│   │   ├── models/   # ORM 模型
│   │   ├── schemas/  # Pydantic 模型
│   │   ├── core/     # 配置/DB/安全
│   │   └── main.py   # 入口
│   ├── data/gtcs.db  # SQLite 数据库
│   └── static/       # 前端构建产物
├── frontend/         # Vue 3 + Element Plus
│   └── src/views/    # 页面组件
├── scripts/          # 工具脚本
└── .claude/          # Claude 项目上下文
```

## 核心模块（12 个 API 路由）
tariff, fta, cost, hs-classification, origin, declaration, screening, price-risk, enterprise, product, audit, dashboard

## 已知限制
- CN 的 NationalTariffLine 为 0 条（tariff 数据只导入了 BR/CA/DE/GB/MX/TW/AU/US/VN/JP/KR）
