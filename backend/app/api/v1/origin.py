from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.origin import OriginAssessment, OriginProfile, OriginBOMDetail
from app.models.product import Product
from app.services.origin_service import (
    calc_rvc_build_down, calc_rvc_build_up,
    check_ctc, check_ctc_from_bom,
    update_rvc_from_bom, run_full_assessment,
    assess_fta_qualification, assess_all_agreements,
)

router = APIRouter(prefix="/origin", tags=["原产地评估"])


@router.get("/assess")
def origin_assess(
    product_id: int = Query(...),
    factory_country: str = Query(...),
    dest_country: str = Query(...),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    profile = db.query(OriginProfile).filter(
        OriginProfile.product_code == product.product_code,
        OriginProfile.manufacturing_country == factory_country.upper(),
        OriginProfile.status == "ACTIVE",
    ).first()

    if not profile:
        return {
            "product_id": product_id,
            "product_name": product.name_cn,
            "factory_country": factory_country,
            "dest_country": dest_country,
            "status": "NOT_ASSESSED",
            "message": "未找到该产品在此产地的原产地评估档案",
        }

    bom_items = db.query(OriginBOMDetail).filter(
        OriginBOMDetail.profile_id == profile.id
    ).all()

    assessments = db.query(OriginAssessment).filter(
        OriginAssessment.product_id == product_id,
        OriginAssessment.factory_country == factory_country.upper(),
        OriginAssessment.dest_country == dest_country.upper(),
    ).order_by(OriginAssessment.id.desc()).first()

    return {
        "product_id": product_id,
        "product_name": product.name_cn,
        "hs_code": product.product_code,
        "factory_country": factory_country,
        "dest_country": dest_country,
        "profile_status": profile.origin_status,
        "applied_criteria": profile.applied_criteria,
        "rvc_calculated": float(profile.rvc_calculated) if profile.rvc_calculated else None,
        "rvc_threshold": float(profile.rvc_threshold) if profile.rvc_threshold else None,
        "cth_met": profile.cth_met,
        "bom_count": len(bom_items),
        "latest_assessment": {
            "result": assessments.result if assessments else None,
            "rvc_value": float(assessments.rvc_value) if assessments and assessments.rvc_value else None,
        } if assessments else None,
    }


@router.post("/rvc/calculate/{profile_id}")
def calculate_rvc(profile_id: int, db: Session = Depends(get_db)):
    """从BOM数据重新计算RVC。"""
    result = update_rvc_from_bom(db, profile_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/assess/{profile_id}")
def full_assessment(profile_id: int, db: Session = Depends(get_db)):
    """对指定profile运行完整原产地评估(RVC+CTC+FTA)。"""
    result = run_full_assessment(db, profile_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/assess/{profile_id}/agreements")
def list_qualified_agreements(profile_id: int, db: Session = Depends(get_db)):
    """列出产品可用的FTA资格。"""
    return assess_all_agreements(db, profile_id)


@router.post("/ctc/check")
def ctc_check(
    hs_code: str = Query(...),
    material_hs_code: str = Query(...),
    level: str = Query("CTH"),
):
    """检查HS编码税则改变 (CC/CTH/CTSH)。"""
    shifted = check_ctc(hs_code, material_hs_code, level)
    return {
        "hs_code": hs_code,
        "material_hs_code": material_hs_code,
        "level": level,
        "shifted": shifted,
    }


@router.get("/profiles")
def list_profiles(
    product_code: Optional[str] = None,
    status: str = "ACTIVE",
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(OriginProfile).filter(OriginProfile.status == status)
    if product_code:
        q = q.filter(OriginProfile.product_code == product_code)
    profiles = q.limit(limit).all()
    return [{
        "id": p.id,
        "product_code": p.product_code,
        "product_name": p.product_name,
        "hs_code": p.hs_code,
        "manufacturing_country": p.manufacturing_country,
        "origin_status": p.origin_status,
        "applied_criteria": p.applied_criteria,
        "rvc_calculated": float(p.rvc_calculated) if p.rvc_calculated else None,
        "valid_from": str(p.valid_from) if p.valid_from else None,
        "valid_to": str(p.valid_to) if p.valid_to else None,
    } for p in profiles]
