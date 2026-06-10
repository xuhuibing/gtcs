---
name: HS 归类工作台
description: 企业级 HS 归类工作台设计 — 上游需求输入 → 预裁定匹配推荐 → 关务确认
type: project
---

# HS 归类工作台

## 工作流程
1. **上游需求输入**：产品名称、描述、品牌、型号、规格、材质、功能、用途、目的国
2. **预裁定匹配**：按关键词搜索各国海关预裁定（product_name / description / key_factors / classification_reasoning）
3. **税则扩展**：若预裁定结果不足 20 条，按关键词搜索 NationalTariffLine 扩展候选
4. **关务确认**：选择 HS 编码 → 按确认按钮 → 保存归类记录 + 税率快照

## API
- `POST /hs-classification/enterprise/recommend` — 推荐（无需权限）
- `POST /hs-classification/enterprise/classify` — 确认（需 admin/customs_mgr/customs_staff/compliance）

## 预裁定匹配逻辑
- 关键词拆分为独立 tokens（中英文混排）
- 每个 token 对 pre-ruling 的 4 个字段做 ILIKE 匹配
- 命中词越多排名越前
- 预裁定匹配的结果优先展示（排序 key: 有预裁定 > 无预裁定 > MFN 税率降序）

## 预裁定数据
共 9 条 seed 数据，来源包含中国海关总署、美国 CBP、欧盟 EBTI、越南海关、日本税关
