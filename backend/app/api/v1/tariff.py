from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.tariff_service import (
    lookup_tariff, search_hs, browse_tariff_lines,
    get_tariff_countries, get_hs_chapters_with_descriptions,
)
from app.schemas.tariff import TariffLookupResponse, HSSearchResult

router = APIRouter(prefix="/tariff", tags=["Tariff"])


@router.get("/countries")
def tariff_countries(db: Session = Depends(get_db)):
    """获取有税则数据的国家列表及数据量统计"""
    return get_tariff_countries(db)


@router.get("/chapters")
def tariff_chapters(
    country: str = Query("US", description="Country ISO2"),
    db: Session = Depends(get_db),
):
    """获取指定国家税则的 HS 章节统计及中英文描述"""
    return get_hs_chapters_with_descriptions(db, country)


@router.get("/browse")
def tariff_browse(
    country: str = Query("US", description="Country ISO2"),
    prefix: Optional[str] = Query(None, description="HS code prefix (e.g. 85)"),
    q: Optional[str] = Query(None, description="Keyword search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """按国家分页浏览税则数据"""
    return browse_tariff_lines(db, country, prefix, q, page, page_size)


@router.get("/lookup", response_model=TariffLookupResponse)
def tariff_lookup(
    hs_code: str = Query(..., description="HS code (e.g. 8528.5200)"),
    dest_country: str = Query(..., description="Destination country ISO2 (e.g. US)"),
    origin_country: str = Query("CN", description="Origin country ISO2"),
    value_usd: Optional[float] = Query(None, description="Value in USD for duty estimation"),
    db: Session = Depends(get_db),
):
    result = lookup_tariff(db, hs_code, dest_country, origin_country)
    if not result:
        raise HTTPException(status_code=404, detail=f"No tariff data for {hs_code} in {dest_country}")

    if value_usd and result.get("total_effective_rate"):
        from decimal import Decimal
        result["estimated_duty"] = (Decimal(str(value_usd)) * result["total_effective_rate"] / Decimal("100")).quantize(Decimal("0.01"))

    return result


@router.get("/search", response_model=list[HSSearchResult])
def tariff_search(
    q: str = Query(..., min_length=2, description="HS code prefix or keyword"),
    country: str = Query("US", description="Country ISO2"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    return search_hs(db, q, country, limit)
