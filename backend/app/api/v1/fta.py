from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.fta_optimizer import recommend_fta, compare_origins

router = APIRouter(prefix="/fta", tags=["FTA"])


@router.get("/recommend")
def fta_recommend(
    hs_code: str = Query(...),
    origin: str = Query("CN"),
    dest: str = Query("US"),
    db: Session = Depends(get_db),
):
    return recommend_fta(db, hs_code, origin, dest)


@router.get("/compare-origins")
def fta_compare_origins(
    hs_code: str = Query(...),
    dest: str = Query("US"),
    origins: Optional[str] = Query(None, description="Comma-separated: CN,VN,TH,MY,ID"),
    db: Session = Depends(get_db),
):
    origin_list = origins.split(",") if origins else None
    return compare_origins(db, hs_code, dest, origin_list)
