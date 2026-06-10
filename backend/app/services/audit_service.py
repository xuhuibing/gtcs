"""审计日志服务"""
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_audit(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    record = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(record)
    db.commit()
    return record


def get_audit_logs(
    db: Session,
    limit: int = 50,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> list:
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    return q.order_by(AuditLog.id.desc()).limit(limit).all()
