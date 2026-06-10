from __future__ import annotations
"""受限制方筛查模型 — OFAC SDN / BIS 实体清单 / EU 制裁 / UN 制裁"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, func
from app.core.database import Base, TimestampMixin


class ScreeningList(Base, TimestampMixin):
    """受限制方名单"""
    __tablename__ = "screening_list"
    id = Column(Integer, primary_key=True)
    list_type = Column(String(20), nullable=False, index=True)  # OFAC / BIS / EU / UN / UK
    id_type = Column(String(20))  # ENTITY / INDIVIDUAL
    name = Column(String(500), nullable=False, index=True)
    name_cn = Column(String(500))
    alias = Column(Text)  # JSON array of aliases
    country = Column(String(10))
    city = Column(String(200))
    address = Column(String(500))
    passport_country = Column(String(10))
    program = Column(String(200))  # 制裁项目 (e.g. IRAN, SYRIA, UKRAINE)
    reason = Column(String(500))
    source_url = Column(String(500))
    effective_date = Column(Date)
    expiration_date = Column(Date)
    status = Column(String(20), default="ACTIVE")  # ACTIVE / EXPIRED / REMOVED
    remarks = Column(Text)


class ScreeningLog(Base, TimestampMixin):
    """筛查记录"""
    __tablename__ = "screening_log"
    id = Column(Integer, primary_key=True)
    screened_by = Column(String(100))  # 筛查人
    screened_name = Column(String(500), nullable=False)  # 被筛查的名称
    screened_type = Column(String(50))  # CUSTOMER / SUPPLIER / EMPLOYEE / OTHER
    match_count = Column(Integer, default=0)
    risk_level = Column(String(20))  # HIGH / MEDIUM / LOW / CLEAN
    match_details = Column(Text)  # JSON array of matches
    reference_id = Column(String(100))  # 关联业务 ID (企业/供应商/报关单)
    reference_type = Column(String(50))  # ENTERPRISE / DECLARATION / PRODUCT
    status = Column(String(20), default="COMPLETED")
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    review_result = Column(String(50))  # CLEARED / BLOCKED / PENDING_REVIEW
    review_notes = Column(Text)
