from __future__ import annotations
"""风险管理（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.core.database import Base, TimestampMixin


class RiskEvent(Base, TimestampMixin):
    __tablename__ = "risk_events"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    event_type = Column(String(30), nullable=False)
    # PRICE_ANOMALY / HS_MISCLASSIFICATION / ORIGIN_ISSUE / DOC_INCONSISTENCY / LICENSE_EXPIRY
    severity = Column(String(10))  # CRITICAL / HIGH / MEDIUM / LOW
    title = Column(String(200), nullable=False)
    description = Column(Text)
    related_declaration = Column(String(30))
    related_product = Column(String(30))
    status = Column(String(20), default="OPEN")  # OPEN / IN_PROGRESS / RESOLVED / CLOSED
    discovered_at = Column(Date)
    resolved_at = Column(Date)
    assigned_to = Column(String(50))


class Rectification(Base, TimestampMixin):
    __tablename__ = "rectifications"
    id = Column(Integer, primary_key=True)
    risk_event_id = Column(Integer, ForeignKey("risk_events.id"))
    root_cause = Column(Text)
    corrective_action = Column(Text)
    preventive_action = Column(Text)
    deadline = Column(Date)
    completed_at = Column(Date)
    verified_by = Column(String(50))
    status = Column(String(20), default="PENDING")  # PENDING / COMPLETED / VERIFIED
