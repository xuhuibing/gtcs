"""审计日志 API"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_user
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit", tags=["审计日志"])
auth_required = require_user(["admin", "customs_mgr", "compliance"])


@router.get("/logs")
def audit_logs(
    limit: int = Query(50, ge=1, le=500),
    action: str = None,
    resource_type: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """获取审计日志"""
    logs = get_audit_logs(db, limit, action, resource_type)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at) if log.created_at else None,
        }
        for log in logs
    ]
