from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tariff import AdditionalDuty, NationalTariffLine
from app.services.tariff_service import get_country_id

router = APIRouter(prefix="/additional-duty", tags=["Additional Duty"])


@router.get("/lookup")
def additional_duty_lookup(
    hs_code: str = Query(...),
    dest_country: str = Query("US"),
    origin_country: str = Query("CN"),
    db: Session = Depends(get_db),
):
    country_id = get_country_id(db, dest_country)
    if not country_id:
        return {"duties": [], "total_rate": 0}

    clean_code = hs_code.replace(".", "").replace(" ", "")

    tariff_line = db.query(NationalTariffLine).filter(
        NationalTariffLine.country_id == country_id,
        NationalTariffLine.local_code.like(f"{clean_code}%"),
    ).first()

    if not tariff_line:
        return {"duties": [], "total_rate": 0}

    duties = db.query(AdditionalDuty).filter(
        AdditionalDuty.country_id == country_id,
        AdditionalDuty.tariff_line_id == tariff_line.id,
        AdditionalDuty.target_origin == origin_country.upper(),
    ).all()

    result = []
    total = 0
    for d in duties:
        rate = float(d.rate_pct or 0)
        total += rate
        result.append({
            "duty_type": d.duty_type,
            "rate_pct": rate,
            "legal_basis": d.legal_basis,
            "case_number": d.case_number,
            "effective_from": str(d.effective_from) if d.effective_from else None,
        })

    return {"hs_code": hs_code, "dest_country": dest_country, "origin": origin_country, "duties": result, "total_rate": total}
