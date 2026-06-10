"""Dashboard stats API"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_user
from app.models.audit import AuditLog
from app.models.tariff import NationalTariffLine
from app.models.country_hs import Country
from app.models.product import Product
from app.models.enterprise import Enterprise
from app.models.declaration import Declaration
from app.models.screening import ScreeningList, ScreeningLog
from app.models.price_risk import PriceAlert
from app.services.fts_service import fts_search

router = APIRouter(prefix="/dashboard", tags=["工作台"])
auth_required = require_user(["admin", "customs_mgr", "customs_staff", "compliance", "viewer"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """获取工作台统计数据"""
    return {
        "countries": db.query(Country).count(),
        "tariff_lines": db.query(NationalTariffLine).count(),
        "tariff_by_country": [
            {"iso2": row.iso2, "name_cn": row.name_cn, "line_count": row.line_count}
            for row in db.query(
                Country.iso2, Country.name_cn,
                func.count(NationalTariffLine.id).label("line_count")
            ).outerjoin(NationalTariffLine).group_by(Country.id).having(
                func.count(NationalTariffLine.id) > 0
            ).order_by(Country.iso2).all()
        ],
        "screening_list_types": [
            {"list_type": r.list_type, "count": r.count}
            for r in db.query(
                ScreeningList.list_type, func.count(ScreeningList.id).label("count")
            ).filter(ScreeningList.status == "ACTIVE"
            ).group_by(ScreeningList.list_type).all()
        ],
        "screening_log_count": db.query(ScreeningLog).count(),
        "screening_high_risk": db.query(ScreeningLog).filter(
            ScreeningLog.risk_level == "HIGH"
        ).count(),
        "enterprises": db.query(Enterprise).count(),
        "products": db.query(Product).count(),
        "declarations": db.query(Declaration).count(),
        "active_alerts": db.query(PriceAlert).filter(
            PriceAlert.status == "ACTIVE"
        ).count(),
        "recent_audit_logs": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "created_at": str(log.created_at) if log.created_at else None,
            }
            for log in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10).all()
        ],
    }


@router.get("/search")
def global_search(
    q: str,
    limit: int = 10,
    current_user=Depends(auth_required),
):
    """全局搜索（FTS5 HS Code + 制裁名单）"""
    results = {"tariff": [], "screening": []}
    if q:
        try:
            results["tariff"] = fts_search("tariff_fts", q, limit)
        except Exception:
            pass
        try:
            results["screening"] = fts_search("screening_fts", q, limit)
        except Exception:
            pass
    return results
