---
name: 预裁定数据库
description: 各国海关预裁定 seed 数据的字段结构和内容
type: project
---

# 预裁定数据库 — HSRulingReference

## 字段
- `country`: CN/US/DE/VN/JP
- `hs_code`: 完整 8 位编码（如 85285200）
- `product_name` / `product_description`: 产品描述（中/英文）
- `ruling_number`: 裁定编号
- `ruling_type`: CN_PRE_CLASSIFICATION / US_CBP_RULING / EU_EBTI
- `issuing_authority`: 发布机构
- `ruling_date` / `expiry_date`: 有效期限
- `decision`: 归类结论
- `classification_reasoning`: 归类推理过程（用于关键词匹配）
- `key_factors`: 关键归类因素
- `legal_basis`: 法律依据（GRI 等）
- `source_url`: 来源链接

## Seed 数据（9 条）
| 国家 | HS | 产品 |
|------|----|------|
| CN | 85285200 | 交互式智能平板(触控一体机) |
| CN | 84714190 | 工业控制计算机(工控机) |
| CN | 85176299 | 5G CPE无线终端 |
| US | 85285900 | Interactive Flat Panel Display |
| US | 84713001 | Tablet Computer with Keyboard |
| DE | 85284900 | Laser Projector for Classroom |
| DE | 85414300 | Photovoltaic Solar Panel |
| VN | 85285900 | Màn hình LCD 75 inch |
| JP | 85258900 | Industrial Camera Module |
