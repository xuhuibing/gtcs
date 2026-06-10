from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.core.database import get_db
from app.services.price_risk_service import (
    create_price_record, recalculate_baseline, get_price_history, get_alerts
)

router = APIRouter(prefix="/price-risk", tags=["价格风控"])


class PriceRecordIn(BaseModel):
    hs_code: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[str] = None
    direction: str = "IMPORT"
    origin_country: Optional[str] = None
    dest_country: Optional[str] = None
    unit_price: float
    currency: str = "USD"
    unit_price_usd: Optional[float] = None
    price_term: Optional[str] = None
    quantity: Optional[float] = None
    total_value: Optional[float] = None
    unit: Optional[str] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    is_related_party: bool = False
    declaration_no: Optional[str] = None
    invoice_no: Optional[str] = None
    contract_no: Optional[str] = None
    shipment_date: Optional[date] = None
    declaration_date: Optional[date] = None


@router.post("/record")
def add_price_record(body: PriceRecordIn, db: Session = Depends(get_db)):
    record = create_price_record(db, body.model_dump())
    return {
        "id": record.id,
        "risk_flag": record.risk_flag,
        "risk_reason": record.risk_reason,
        "hs_code": record.hs_code,
        "unit_price": float(record.unit_price),
    }


@router.get("/history")
def price_history(
    hs_code: str = Query(...),
    brand: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return get_price_history(db, hs_code, brand=brand, model=model, limit=limit)


@router.get("/alerts")
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return get_alerts(db, status=status, severity=severity, limit=limit)


@router.post("/baseline/recalculate")
def recalculate(
    hs_code: str = Query(...),
    direction: str = "IMPORT",
    brand: Optional[str] = None,
    model: Optional[str] = None,
    db: Session = Depends(get_db),
):
    baseline = recalculate_baseline(db, hs_code, direction, brand, model)
    if not baseline:
        return {"status": "NO_DATA", "message": "无足够历史数据计算基线"}
    return {
        "id": baseline.id,
        "hs_code": baseline.hs_code,
        "avg_price": float(baseline.avg_price),
        "min_price": float(baseline.min_price),
        "max_price": float(baseline.max_price),
        "std_deviation": float(baseline.std_deviation),
        "sample_count": baseline.sample_count,
        "alert_low_price": float(baseline.alert_low_price),
        "alert_high_price": float(baseline.alert_high_price),
        "threshold_source": baseline.threshold_source,
    }


@router.post("/batch")
def batch_import(records: List[PriceRecordIn], db: Session = Depends(get_db)):
    results = []
    for item in records:
        record = create_price_record(db, item.model_dump())
        results.append({
            "id": record.id,
            "risk_flag": record.risk_flag,
            "hs_code": record.hs_code,
            "unit_price": float(record.unit_price),
        })
    return {"imported": len(results), "records": results}
