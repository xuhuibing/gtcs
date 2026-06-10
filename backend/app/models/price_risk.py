from __future__ import annotations
from typing import Optional, List, Dict, Any
"""价格风控 — 从 app/models/price_risk.py 迁移"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, Boolean, ForeignKey, func
from app.core.database import Base, TimestampMixin


class PriceRecord(Base, TimestampMixin):
    """进出口价格记录"""
    __tablename__ = "price_record"
    id = Column(Integer, primary_key=True)
    product_code = Column(String(30))
    product_name = Column(String(200))
    brand = Column(String(50))
    model = Column(String(100))
    hs_code = Column(String(15), nullable=False)
    specifications = Column(String(200))
    direction = Column(String(10), nullable=False)  # EXPORT / IMPORT
    origin_country = Column(String(2))
    dest_country = Column(String(2))
    customs_port = Column(String(20))
    unit_price = Column(Numeric(12, 4), nullable=False)
    currency = Column(String(3), default="USD")
    unit_price_usd = Column(Numeric(12, 4))
    price_term = Column(String(10))  # FOB / CIF / CFR / EXW
    quantity = Column(Numeric(12, 2))
    total_value = Column(Numeric(14, 2))
    unit = Column(String(20))
    buyer = Column(String(200))
    seller = Column(String(200))
    is_related_party = Column(Boolean, default=False)
    declaration_no = Column(String(30))
    invoice_no = Column(String(50))
    contract_no = Column(String(50))
    shipment_date = Column(Date)
    declaration_date = Column(Date, nullable=False)
    risk_flag = Column(String(20), default="NORMAL")
    risk_reason = Column(Text)
    reviewed = Column(Boolean, default=False)


class PriceBaseline(Base, TimestampMixin):
    """价格基线"""
    __tablename__ = "price_baseline"
    id = Column(Integer, primary_key=True)
    product_code = Column(String(30))
    product_name = Column(String(200))
    brand = Column(String(50))
    model = Column(String(100))
    hs_code = Column(String(15), nullable=False)
    direction = Column(String(10), nullable=False)
    dest_country = Column(String(2))
    avg_price = Column(Numeric(12, 4))
    min_price = Column(Numeric(12, 4))
    max_price = Column(Numeric(12, 4))
    std_deviation = Column(Numeric(12, 4))
    median_price = Column(Numeric(12, 4))
    sample_count = Column(Integer)
    currency = Column(String(3), default="USD")
    price_term = Column(String(10))
    alert_low_price = Column(Numeric(12, 4))
    alert_high_price = Column(Numeric(12, 4))
    alert_change_pct = Column(Numeric(6, 2))
    threshold_source = Column(String(20))
    customs_ref_price_low = Column(Numeric(12, 4))
    customs_ref_price_high = Column(Numeric(12, 4))
    valid_from = Column(Date)
    valid_to = Column(Date)
    last_calculated = Column(DateTime)


class PriceAlert(Base, TimestampMixin):
    """价格预警记录"""
    __tablename__ = "price_alert"
    id = Column(Integer, primary_key=True)
    price_record_id = Column(Integer, ForeignKey("price_record.id"))
    baseline_id = Column(Integer, ForeignKey("price_baseline.id"))
    alert_type = Column(String(30), nullable=False)
    current_price = Column(Numeric(12, 4))
    baseline_price = Column(Numeric(12, 4))
    deviation_pct = Column(Numeric(8, 2))
    deviation_amount = Column(Numeric(12, 4))
    previous_price = Column(Numeric(12, 4))
    previous_date = Column(Date)
    severity = Column(String(10))  # HIGH / MEDIUM / LOW
    risk_description = Column(Text)
    customs_implication = Column(Text)
    suggested_action = Column(Text)
    status = Column(String(20), default="PENDING")
    handled_by = Column(String(50))
    resolution = Column(Text)
    triggered_at = Column(DateTime, server_default=func.now())


class PriceJustification(Base, TimestampMixin):
    """价格合理性说明"""
    __tablename__ = "price_justification"
    id = Column(Integer, primary_key=True)
    price_record_id = Column(Integer, ForeignKey("price_record.id"))
    reason_type = Column(String(30), nullable=False)
    explanation = Column(Text, nullable=False)
    supporting_evidence = Column(Text)
    attachment_refs = Column(Text)
    prepared_by = Column(String(50))
    approved_by = Column(String(50))
    approved_date = Column(Date)
