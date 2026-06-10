from __future__ import annotations
from typing import Optional, List, Dict, Any
"""审计日志 + 汇率 + 采集日志（从 app/ 迁移，合并 gtcs-server 的 audit_log）"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, func
from app.core.database import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(50))
    action = Column(String(50), nullable=False)  # LOGIN / QUERY / CREATE / UPDATE / DELETE / EXPORT
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    detail = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class ExchangeRate(Base, TimestampMixin):
    __tablename__ = "exchange_rate"
    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(12, 6), nullable=False)
    rate_date = Column(Date, nullable=False)
    source = Column(String(50))


class CostSimulation(Base, TimestampMixin):
    __tablename__ = "cost_simulation"
    id = Column(Integer, primary_key=True)
    hs_code = Column(String(15), nullable=False)
    dest_country = Column(String(2), nullable=False)
    scenarios = Column(Text)  # JSON
    result = Column(Text)  # JSON
    created_by = Column(String(50))


class CollectionLog(Base, TimestampMixin):
    __tablename__ = "collection_log"
    id = Column(Integer, primary_key=True)
    collector_name = Column(String(50), nullable=False)
    status = Column(String(20))  # SUCCESS / FAILED / PARTIAL
    records_collected = Column(Integer)
    error_message = Column(Text)
    duration_seconds = Column(Integer)
