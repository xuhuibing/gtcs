from __future__ import annotations
"""受限制方筛查 API — 制裁名单匹配检查"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_user
from app.services.screening_service import (
    screen_name, screen_batch, log_screening,
    get_screening_lists, get_screening_logs,
)

router = APIRouter(prefix="/screening", tags=["受限制方筛查"])

# 登录校验依赖
auth_required = require_user(["admin", "customs_mgr", "customs_staff", "compliance", "viewer"])


class ScreeningCheckRequest(BaseModel):
    name: str
    name_cn: Optional[str] = None
    screened_type: str = "OTHER"
    list_types: Optional[List[str]] = None
    min_score: float = 60.0
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class BatchScreeningRequest(BaseModel):
    names: List[ScreeningCheckRequest]
    list_types: Optional[List[str]] = None
    min_score: float = 60.0


@router.post("/check")
def screening_check(
    body: ScreeningCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """对单个名称做受限制方筛查"""
    all_results = []
    for n in [body.name] + ([body.name_cn] if body.name_cn else []):
        matches = screen_name(db, n, body.list_types, body.min_score)
        all_results.extend(matches)

    seen_ids = set()
    unique = []
    for m in all_results:
        if m["match_id"] not in seen_ids:
            seen_ids.add(m["match_id"])
            unique.append(m)
    unique.sort(key=lambda x: x["score"], reverse=True)

    log_screening(
        db, body.name, body.screened_type, unique,
        body.reference_id, body.reference_type,
        screened_by=current_user.display_name or current_user.username,
    )

    return {
        "screened_name": body.name,
        "screened_name_cn": body.name_cn,
        "match_count": len(unique),
        "risk_level": _get_level(unique),
        "matches": unique,
    }


@router.post("/batch")
def screening_batch(
    body: BatchScreeningRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """批量筛查多个名称"""
    all_names = []
    for item in body.names:
        all_names.append(item.name)
        if item.name_cn:
            all_names.append(item.name_cn)

    matches = screen_batch(db, all_names, body.list_types, body.min_score)
    return {"total": len(body.names), "results": matches}


@router.get("/lists")
def screening_list_overview(
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """获取制裁名单概览"""
    return get_screening_lists(db)


@router.get("/history")
def screening_history(
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(auth_required),
):
    """获取筛查历史记录"""
    return get_screening_logs(db, limit, risk_level, status)


def _get_level(matches: list) -> str:
    if not matches:
        return "CLEAN"
    best = max(m["score"] for m in matches)
    if best >= 90:
        return "HIGH"
    elif best >= 75:
        return "MEDIUM"
    return "LOW"
