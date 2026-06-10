from __future__ import annotations
from typing import Optional, List, Dict, Any
"""原产地 — 规则引擎 + 证据链 + 证书管理

合并 app/models/rules_of_origin.py + app/models/origin_evidence.py (5表) + gtcs-server/models/origin.py
"""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey
from app.core.database import Base, TimestampMixin


class RulesOfOrigin(Base, TimestampMixin):
    """原产地规则 — 协定对HS章节的规则定义"""
    __tablename__ = "rules_of_origin"
    id = Column(Integer, primary_key=True)
    agreement_id = Column(Integer, ForeignKey("trade_agreement.id"))
    hs_code = Column(String(10))
    criteria_type = Column(String(20))  # RVC / CTC / SP / COMBINATION
    threshold_value = Column(String(50))
    rule_text = Column(Text)
    source_url = Column(String(500))


class OriginProfile(Base, TimestampMixin):
    """产品原产地档案 — 每个产品在各地制造地的完整证据链"""
    __tablename__ = "origin_profile"
    id = Column(Integer, primary_key=True)
    product_code = Column(String(30), nullable=False)
    product_name = Column(String(200))
    hs_code = Column(String(15), nullable=False)
    manufacturing_country = Column(String(2), nullable=False)
    assembly_country = Column(String(2))
    origin_status = Column(String(20))  # QUALIFIES / DOES_NOT_QUALIFY / CONDITIONAL / UNDER_REVIEW
    applied_criteria = Column(String(30))
    target_agreement = Column(String(20))
    rvc_calculated = Column(Numeric(6, 2))
    rvc_threshold = Column(Numeric(6, 2))
    rvc_method = Column(String(20))
    cth_met = Column(Boolean)
    substantial_transformation = Column(String(20))
    total_material_cost = Column(Numeric(12, 2))
    local_material_cost = Column(Numeric(12, 2))
    imported_material_cost = Column(Numeric(12, 2))
    labor_cost = Column(Numeric(12, 2))
    overhead_cost = Column(Numeric(12, 2))
    ex_works_price = Column(Numeric(12, 2))
    fob_price = Column(Numeric(12, 2))
    assessed_by = Column(String(50))
    valid_from = Column(Date)
    valid_to = Column(Date)
    risk_level = Column(String(10))
    status = Column(String(20), default="ACTIVE")


class OriginBOMDetail(Base, TimestampMixin):
    """BOM料件原产地明细"""
    __tablename__ = "origin_bom_detail"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("origin_profile.id"), nullable=False)
    material_code = Column(String(30))
    material_name = Column(String(200), nullable=False)
    material_hs_code = Column(String(15))
    material_origin = Column(String(2), nullable=False)
    supplier_name = Column(String(200))
    supplier_country = Column(String(2))
    unit_cost = Column(Numeric(12, 4))
    quantity_per_unit = Column(Numeric(12, 4))
    total_cost = Column(Numeric(12, 2))
    cost_percentage = Column(Numeric(6, 2))
    is_local = Column(Boolean, default=False)
    is_originating = Column(Boolean, default=False)
    tariff_shift_from = Column(String(6))
    tariff_shift_to = Column(String(6))
    tariff_shift_type = Column(String(10))


class OriginProcessStep(Base, TimestampMixin):
    """制造工序明细"""
    __tablename__ = "origin_process_step"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("origin_profile.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    process_name = Column(String(100), nullable=False)
    process_description = Column(Text)
    process_country = Column(String(2), nullable=False)
    value_added = Column(Numeric(12, 2))
    value_added_percentage = Column(Numeric(6, 2))
    is_substantial = Column(Boolean)
    is_simple_operation = Column(Boolean, default=False)


class OriginCostBreakdown(Base, TimestampMixin):
    """成本分解表 — RVC 计算底稿"""
    __tablename__ = "origin_cost_breakdown"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("origin_profile.id"), nullable=False)
    cost_category = Column(String(30), nullable=False)
    cost_item = Column(String(100))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    is_local_value = Column(Boolean, default=False)
    notes = Column(Text)


class OriginCertificate(Base, TimestampMixin):
    """原产地证书"""
    __tablename__ = "origin_certificate"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("origin_profile.id"))
    cert_type = Column(String(20), nullable=False)  # FORM_E / FORM_D / RCEP_CO / EUR1
    cert_number = Column(String(50))
    issuing_authority = Column(String(200))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    dest_country = Column(String(2))
    duty_saved = Column(Numeric(12, 2))
    status = Column(String(20), default="VALID")


class FTAAgreement(Base, TimestampMixin):
    """企业已启用的FTA协定记录（从 gtcs-server 迁移）"""
    __tablename__ = "fta_agreement"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    agreement_code = Column(String(20), nullable=False)
    origin_country = Column(String(2))
    status = Column(String(20), default="ACTIVE")


class OriginAssessment(Base, TimestampMixin):
    """原产地评估记录（从 gtcs-server 迁移）"""
    __tablename__ = "origin_assessment"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    factory_country = Column(String(2), nullable=False)
    dest_country = Column(String(2), nullable=False)
    result = Column(String(20))  # GREEN / YELLOW / RED
    rvc_value = Column(Numeric(6, 2))
    rvc_threshold = Column(Numeric(6, 2))
    assessed_by = Column(String(50))
