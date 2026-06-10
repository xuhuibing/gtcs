from __future__ import annotations
from typing import Optional, List, Dict, Any
"""费用管理（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Date
from app.core.database import Base, TimestampMixin


class FeeQuote(Base, TimestampMixin):
    __tablename__ = "fee_quotes"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    broker_name = Column(String(200), nullable=False)
    service_type = Column(String(50))  # DECLARATION / INSPECTION / CERTIFICATION
    unit_price = Column(Float)
    currency = Column(String(3), default="CNY")
    effective_from = Column(Date)
    effective_to = Column(Date)
    remark = Column(Text)


class FeeBill(Base, TimestampMixin):
    __tablename__ = "fee_bills"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    broker_name = Column(String(200), nullable=False)
    bill_no = Column(String(50), unique=True)
    bill_date = Column(Date)
    total_amount = Column(Float)
    currency = Column(String(3), default="CNY")
    status = Column(String(20), default="PENDING")


class FeeDiff(Base, TimestampMixin):
    __tablename__ = "fee_diffs"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("fee_bills.id"))
    declaration_no = Column(String(30))
    quoted_price = Column(Float)
    billed_price = Column(Float)
    diff_amount = Column(Float)
    reason = Column(String(100))
    status = Column(String(20), default="OPEN")
