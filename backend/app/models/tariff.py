from __future__ import annotations
from typing import Optional, List, Dict, Any
"""税率核心模型 — 合并 app/ 和 gtcs-server 的 tariff 模型

表关系:
  country → national_tariff_line → tariff_rate
                                   → additional_duty
  trade_agreement → tariff_rate (FTA)
                  → rules_of_origin
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, UniqueConstraint, func
from app.core.database import Base, TimestampMixin


class TradeAgreement(Base, TimestampMixin):
    """贸易协定（FTA）"""
    __tablename__ = "trade_agreement"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)  # RCEP / ACFTA / CPTPP / ...
    name_cn = Column(String(200))
    name_en = Column(String(200))
    member_countries = Column(Text)  # JSON array of ISO2 codes
    effective_date = Column(Date)
    type = Column(String(20))  # FTA / GSP / PTA


class NationalTariffLine(Base, TimestampMixin):
    """各国本地税目 (HS 8-10位)"""
    __tablename__ = "national_tariff_line"
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("country.id"), nullable=False)
    local_code = Column(String(15), nullable=False)
    hs6_id = Column(Integer, ForeignKey("hs_nomenclatures.id"))
    description_local = Column(Text)
    description_en = Column(Text)
    description_cn = Column(Text)
    unit = Column(String(50))
    effective_year = Column(Integer)
    data_source_url = Column(String(500))

    __table_args__ = (UniqueConstraint("country_id", "local_code", "effective_year"),)


class TariffRate(Base, TimestampMixin):
    """税率主表（一品多率）"""
    __tablename__ = "tariff_rate"
    id = Column(Integer, primary_key=True)
    tariff_line_id = Column(Integer, ForeignKey("national_tariff_line.id"), nullable=False)
    rate_type = Column(String(20), nullable=False)  # MFN / FTA / COLUMN2 / GSP
    agreement_id = Column(Integer, ForeignKey("trade_agreement.id"))
    origin_scope = Column(String(100))
    ad_valorem_rate = Column(Numeric(8, 4))
    specific_rate = Column(Numeric(12, 4))
    specific_rate_unit = Column(String(50))
    compound_formula = Column(String(200))
    effective_from = Column(Date)
    effective_to = Column(Date)
    source_url = Column(String(500))
    last_updated = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("tariff_line_id", "rate_type", "agreement_id", "origin_scope", "effective_from"),)


class AdditionalDuty(Base, TimestampMixin):
    """附加税（301 / AD / CVD / 232）"""
    __tablename__ = "additional_duty"
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("country.id"), nullable=False)
    tariff_line_id = Column(Integer, ForeignKey("national_tariff_line.id"))
    duty_type = Column(String(20), nullable=False)  # SEC301 / AD / CVD / SECTION232
    rate_pct = Column(Numeric(6, 2))
    rate_formula = Column(String(100))
    target_origin = Column(String(2))  # 针对原产国
    legal_basis = Column(String(200))
    case_number = Column(String(50))
    effective_from = Column(Date)
    effective_to = Column(Date)
    source_url = Column(String(500))
