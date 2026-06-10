from __future__ import annotations
from typing import Optional, List, Dict, Any
"""稽查防控 — 从 app/models/customs_audit.py 迁移"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, Boolean, ForeignKey, func
from app.core.database import Base, TimestampMixin


class RoyaltyRecord(Base, TimestampMixin):
    """特许权使用费台账"""
    __tablename__ = "royalty_record"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    royalty_type = Column(String(30))  # BRAND / PATENT / TECHNOLOGY
    payee_name = Column(String(200))
    contract_no = Column(String(50))
    payment_date = Column(Date)
    amount = Column(Numeric(14, 2))
    currency = Column(String(3), default="USD")
    related_to_import = Column(Boolean)  # 是否与进口货物相关
    related_products = Column(Text)
    reasoning = Column(Text)
    included_in_dutiable = Column(Boolean, default=False)
    declared_value = Column(Numeric(14, 2))
    reviewed_by = Column(String(50))
    status = Column(String(20), default="ACTIVE")


class AssistRecord(Base, TimestampMixin):
    """协助费台账 (免费提供的模具/图纸/技术)"""
    __tablename__ = "assist_record"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    assist_type = Column(String(30))  # MOLD / DRAWING / TECHNOLOGY
    description = Column(Text)
    provider = Column(String(200))
    provided_date = Column(Date)
    fair_value = Column(Numeric(14, 2))
    apportionment_method = Column(String(100))
    apportioned_amount = Column(Numeric(14, 2))
    included_in_dutiable = Column(Boolean, default=False)
    status = Column(String(20), default="ACTIVE")


class DocumentConsistencyCheck(Base, TimestampMixin):
    """单证一致性校验记录"""
    __tablename__ = "document_consistency_check"
    id = Column(Integer, primary_key=True)
    declaration_id = Column(Integer, ForeignKey("declarations.id"))
    check_type = Column(String(30))  # DECL_VS_INVOICE / HS_CROSS_COUNTRY
    total_rules = Column(Integer)
    passed_count = Column(Integer)
    overall_pass = Column(Boolean)
    details = Column(Text)  # JSON
    checked_by = Column(String(50))
    checked_at = Column(DateTime, server_default=func.now())


class AEOScorecard(Base, TimestampMixin):
    """AEO信用评分卡"""
    __tablename__ = "aeo_scorecard"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    score_date = Column(Date, nullable=False)
    internal_control_score = Column(Numeric(5, 2))
    financial_score = Column(Numeric(5, 2))
    legal_compliance_score = Column(Numeric(5, 2))
    trade_security_score = Column(Numeric(5, 2))
    total_score = Column(Numeric(5, 2))
    risk_level = Column(String(10))
    notes = Column(Text)
