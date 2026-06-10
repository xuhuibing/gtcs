from __future__ import annotations
from typing import Optional, List, Dict, Any
"""企业信息（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.core.database import Base, TimestampMixin


class Enterprise(Base, TimestampMixin):
    __tablename__ = "enterprises"
    id = Column(Integer, primary_key=True)
    name_cn = Column(String(200), nullable=False)
    name_en = Column(String(200))
    credit_code = Column(String(20), unique=True)
    customs_code = Column(String(20), unique=True)
    aeo_level = Column(String(20))  # ADVANCED / CERTIFIED / NORMAL
    address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(30))


class Factory(Base, TimestampMixin):
    __tablename__ = "factories"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    name = Column(String(200), nullable=False)
    country = Column(String(2), nullable=False)
    address = Column(Text)
    is_primary = Column(Integer, default=0)


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    name = Column(String(200), nullable=False)
    country = Column(String(2))
    supplier_type = Column(String(50))  # raw_material / component / service
    risk_level = Column(String(10))  # HIGH / MEDIUM / LOW


class License(Base, TimestampMixin):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    license_type = Column(String(50), nullable=False)
    license_no = Column(String(100))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    status = Column(String(20), default="VALID")
