# GTCS 全球贸易通关系统 — 实施总结

## 项目概述

**GTCS (Global Trade Customs Clearance System)** 是一个基于 Python FastAPI 的全栈贸易通关决策平台，提供税则查询、FTA 原产地优选、进口成本模拟、HS 归类辅助、价格风控、原产地规则评估(RVC/CTC)、报关单全生命周期管理等功能。

- **版本**: v2.0.0
- **框架**: FastAPI + SQLAlchemy 2.0 + Vue 3 (Element Plus)
- **数据库**: SQLite (17.6 MB)
- **运行端口**: 8008 (API) / 5173 (Dev) / 80 (Prod)

---

## 已实现功能模块 (12个 API 模块)

### 1. 税则查询与税率速查 `/api/v1/tariff/`
- `GET /lookup` — 综合税则查询(含 MFN、FTA、附加税)
- `GET /search` — HS 编码模糊搜索
- 支持 4 国家税则库: US (29,581 条) + VN (14,453 条) + TH (14,425 条) + MY (13,501 条)
- US 税率: 36,862 条 (General/Column2/Special)
- Section 301 附加税: 1,667 条

### 2. FTA 原产地优选 `/api/v1/fta/`
- `GET /recommend` — 最优 FTA 推荐 (8项贸易协定)
- `GET /compare-origins` — 多原产国对比分析
- 支持的协定: RCEP, ACFTA, CPTPP, USMCA, EVFTA, EU_GSP, AIFTA, KAFTA
- 含证书要求与 ROO 规则说明

### 3. 进口成本模拟 `/api/v1/cost/`
- `POST /simulate` — FOB→CIF→完税成本全链路模拟
- 支持: 关税/附加税/增值税/报关费/港杂费

### 4. HS 归类辅助 `/api/v1/hs-classification/`
- `POST /classify` — HS 归类记录
- `GET /search` — HS 编码搜索
- `GET /history` — 历史归类记录
- `GET /rulings` — 归类裁定查询
- `GET /consistency-check` — HS 编码一致性检查

### 5. 价格风控引擎 `/api/v1/price-risk/`
- `POST /record` — 价格记录录入(含6类风险规则)
- `GET /history` — 历史价格曲线
- `GET /alerts` — 风险告警列表
- `POST /baseline/recalculate` — 基线重新计算
- `POST /batch` — 批量导入
- 告警类型: BELOW_FLOOR / ABOVE_CEILING / SUDDEN_DROP / SUDDEN_SPIKE / RELATED_PARTY_DEVIATION / CROSS_PORT_INCONSISTENCY

### 6. 原产地评估 `/api/v1/origin/`
- `GET /assess` — 原产地综合评估
- `GET /profiles` — 原产地档案列表
- `POST /rvc/calculate/:id` — RVC 计算(扣减法/累加法/净成本法)
- `POST /assess/:id` — 完整评估 (RVC+CTC+FTA)
- `GET /assess/:id/agreements` — FTA 资格评估
- `POST /ctc/check` — CTC 税则改变检查 (CC/CTH/CTSH)

### 7. 报关单管理 `/api/v1/declaration/`
- 状态机: draft → submitted → query_received → amended → cleared → closed
- `POST /create` — 新建报关单
- `GET /list` — 报关单列表(含筛选)
- `GET /:id` — 报关单详情
- `POST /:id/transition` — 状态变更
- `POST /:id/check` — 申报前一致性检查
- `POST /consistency/check` — 独立一致性检查

### 8. 附加税查询 `/api/v1/additional-duty/`
- `GET /lookup` — 附加税查询(301/AD/CVD/232)

### 9. 认证授权 `/api/v1/auth/`
- `POST /login` — JWT 登录
- `POST /register` — 用户注册
- `GET /profile` — 用户信息

### 10. 企业管理 `/api/v1/enterprise/`
- 企业/工厂/供应商/资质管理

### 11. 产品管理 `/api/v1/product/`
- 产品/HS 映射/分类管理

### 12. 系统管理
- `GET /health` — 健康检查
- `/docs` — Swagger 文档

---

## 数据源

### 税则库数据 (来源: `税则库/` 目录)
| 国家 | 来源 | 税目数 | 说明 |
|------|------|--------|------|
| 美国(US) | data.zip → hts.db (hts_subheadings + hts_rates + s122_exempt) | 29,581 | 含36,862条税率、1,667条S301附加税 |
| 越南(VN) | hts_source.db (vn_tariff_items) | 14,453 | 含30+种FTA税率 |
| 泰国(TH) | THAI.zip (JSONL) | 14,425 | 含英泰双语描述 |
| 马来西亚(MY) | hts_source.db (my_tariff_items) | 13,501 | 常规税则 |

**排除**: `china_tariff_2026.pdf` (用户指定 PDF 不导入)

### 贸易协定 (8项)
RCEP, ACFTA, CPTPP, USMCA, EVFTA, EU_GSP, AIFTA, KAFTA

### 系统数据
- 15 个国家基础数据
- 默认管理员: admin / admin123

---

## 技术架构

```
backend/
├── app/
│   ├── api/v1/         # 12个路由模块 (26+ endpoints)
│   ├── core/           # 数据库/配置/安全
│   ├── models/         # 14个 SQLAlchemy 模型
│   ├── schemas/        # Pydantic 请求/响应模型
│   └── services/       # 6个业务服务层
├── scripts/
│   ├── import_tariff_data.py  # 税则数据导入 (v2)
│   └── seed_data.py           # 种子数据初始化
├── frontend/           # Vue 3 + Element Plus SPA (11个页面)
├── data/               # SQLite 数据库
├── static/             # 前端构建产物
├── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

### 数据库核心表 (18张)
1. `country` — 国家数据
2. `hs_nomenclature` — HS 编码骨架
3. `national_tariff_line` — 各国本地税目
4. `tariff_rate` — 税率主表(一品多率)
5. `additional_duty` — 附加税表
6. `trade_agreement` — 贸易协定
7. `rules_of_origin` — 原产地规则
8. `origin_profile` — 产品原产地档案
9. `origin_bom_detail` — BOM料件明细
10. `origin_process_step` — 制造工序
11. `origin_cost_breakdown` — 成本分解
12. `origin_certificate` — 原产地证书
13. `origin_assessment` — 原产地评估记录
14. `declarations` — 报关单主表
15. `declaration_items` — 报关单项明细
16. `price_record` — 价格记录
17. `price_baseline` — 价格基线
18. `price_alert` — 价格告警

---

## 已知问题与改进点

### 已修复
- US 税率与税目关联错误 (rate_batch 未写入数据库)
- Python 3.9 类型注解兼容性 (`X | None` → `Optional[X]`)
- OpenAPI 模型渲染 (ForwardRef 问题)
- 表名单复数不匹配
- 字段名与旧数据库不匹配

### 待改进
1. **中国税则导入** — PDF 解析 (当前用户指定跳过)
2. **ID/JP/KR 等国税则** — hts_source.db 含31国表，可逐步导入
3. **性能优化** — SQLite 不适合高并发，建议迁移 PostgreSQL
4. **搜索增强** — 全文索引支持中文商品名搜索
5. **测试覆盖** — 增加 pytest 自动化测试
6. **CI/CD** — GitHub Actions 自动部署
7. **HTTPS** — Let's Encrypt 证书配置
8. **数据备份** — SQLite 自动备份/归档策略

---

## 启动方式

```bash
# 开发环境
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8008

# 前端开发 (另一个终端)
cd frontend
npm run dev

# 生产部署
docker-compose up -d
```

---

*生成日期: 2026-06-09 | 系统: GTCS v2.0.0*
