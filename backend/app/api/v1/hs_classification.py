from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.core.database import get_db
from app.core.security import require_user
from app.services.hs_classification_service import (
    create_classification, get_classification, search_rulings, check_consistency
)
from app.services.tariff_service import lookup_tariff
from app.models.compliance import HSRulingReference, HSClassificationRecord
from app.models.country_hs import Country
from app.models.tariff import NationalTariffLine

router = APIRouter(prefix="/hs-classification", tags=["HS归类档案"])


class ClassificationIn(BaseModel):
    classified_hs_code: str
    product_code: Optional[str] = None
    product_name_cn: Optional[str] = None
    product_name_en: Optional[str] = None
    product_description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[str] = None
    material_composition: Optional[str] = None
    function_description: Optional[str] = None
    use_purpose: Optional[str] = None
    classified_country_id: Optional[int] = None
    classification_basis: str = "SELF_CLASSIFY"
    confidence_level: str = "MEDIUM"
    ruling_number: Optional[str] = None
    ruling_country: Optional[str] = None
    ruling_date: Optional[date] = None
    ruling_hs_code: Optional[str] = None
    ruling_product_description: Optional[str] = None
    ruling_key_reasoning: Optional[str] = None
    ruling_source_url: Optional[str] = None
    classification_notes: Optional[str] = None
    key_classification_factors: Optional[str] = None
    alternative_hs_codes: Optional[str] = None
    rejection_reasons: Optional[str] = None
    classified_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


@router.post("/record")
@router.post("/classify")
def add_classification(body: ClassificationIn, db: Session = Depends(get_db)):
    record = create_classification(db, body.model_dump())
    return {
        "id": record.id,
        "product_code": record.product_code,
        "classified_hs_code": record.classified_hs_code,
        "classification_basis": record.classification_basis,
        "status": record.status,
    }


# ─── 企业级归类工作台 API ───

class EnterpriseClassifyRequest(BaseModel):
    product_name: str = ""
    product_description: str = ""
    brand: str = ""
    model: str = ""
    specifications: str = ""
    material_composition: str = ""
    function_description: str = ""
    use_purpose: str = ""
    dest_country: str = "CN"
    hs_code_candidate: Optional[str] = None  # 关务选择的HS


@router.post("/enterprise/recommend")
def enterprise_recommend(
    body: EnterpriseClassifyRequest,
    db: Session = Depends(get_db),
):
    """接受上游产品需求 → 推荐 HS 编码 + 匹配预裁定 + 对应税率"""
    results = []
    seen_hs = set()
    query_text = " ".join(filter(None, [body.product_name, body.function_description, body.product_description]))

    if not query_text:
        return {"product_name": body.product_name, "dest_country": body.dest_country, "recommendations": []}

    # 从查询文本提取有意义的词（中英文混排，拆分为独立 tokens）
    terms = [t for t in query_text.replace(",", " ").replace("，", " ").replace("/", " ").split() if len(t) > 1][:8]

    def _make_ruling_list(rulings):
        return [
            {
                "ruling_number": r.ruling_number,
                "ruling_type": r.ruling_type,
                "issuing_authority": r.issuing_authority,
                "product_name": r.product_name,
                "decision": r.decision,
                "classification_reasoning": r.classification_reasoning,
                "ruling_date": str(r.ruling_date),
            }
            for r in rulings
        ]

    def _make_result_entry(hs, hs_full, desc_cn, desc_en, matched_rulings, tariff):
        return {
            "hs_code": hs,
            "hs_code_full": hs_full,
            "description_cn": desc_cn,
            "description_en": desc_en,
            "mfn_rate": float(tariff.get("mfn_rate", 0)) if tariff and tariff.get("mfn_rate") else None,
            "fta_rates": [
                {"agreement": f.get("agreement"), "rate_pct": float(f.get("rate_pct", 0))}
                for f in (tariff.get("fta_rates", []) if tariff else [])
            ] if tariff else [],
            "total_effective_rate": float(tariff.get("total_effective_rate", 0)) if tariff else None,
            "matched_rulings": matched_rulings,
        }

    # 1. 匹配海关预裁定数据库（首选 — 精度最高）
    if terms:
        ruling_filters = []
        for t in terms:
            ruling_filters.append(HSRulingReference.product_name.ilike(f"%{t}%"))
            ruling_filters.append(HSRulingReference.product_description.ilike(f"%{t}%"))
            ruling_filters.append(HSRulingReference.key_factors.ilike(f"%{t}%"))
            ruling_filters.append(HSRulingReference.classification_reasoning.ilike(f"%{t}%"))
        # 使用 match count 排序：命中词越多的预裁定排越前
        ruling_matches = db.query(HSRulingReference).filter(
            or_(*ruling_filters)
        ).limit(20).all()

        for r in ruling_matches:
            hs = r.hs_code[:6]
            if hs in seen_hs:
                continue
            seen_hs.add(hs)
            tariff = lookup_tariff(db, hs, body.dest_country, "CN")
            # 有预裁定时，用预裁定的产品名称作为商品描述，避免空列
            results.append(_make_result_entry(
                hs, r.hs_code,
                r.product_name, r.product_description or "",
                _make_ruling_list([r]), tariff,
            ))

    # 2. 从 NationalTariffLine 搜索（关键词 → 扩展候选编码）
    if terms and len(seen_hs) < 20:
        t_filters = []
        for t in terms:
            t_filters.append(NationalTariffLine.description_en.ilike(f"%{t}%"))
            t_filters.append(NationalTariffLine.description_cn.ilike(f"%{t}%"))

        q = db.query(NationalTariffLine).filter(or_(*t_filters))

        # 尝试按目的国筛选，如果无数据则扫全部
        cid = None
        if body.dest_country:
            cid = db.query(Country.id).filter(Country.iso2 == body.dest_country.upper()).scalar()
        if cid:
            country_lines = q.filter(NationalTariffLine.country_id == cid).limit(20).all()
            lines = country_lines if country_lines else q.limit(30).all()
        else:
            lines = q.limit(30).all()

        for line in lines:
            hs = line.local_code[:6]
            if hs in seen_hs:
                continue
            seen_hs.add(hs)
            tariff = lookup_tariff(db, hs, body.dest_country, "CN")
            match_rulings = db.query(HSRulingReference).filter(
                HSRulingReference.hs_code.like(f"{hs}%"),
            ).limit(3).all()
            results.append(_make_result_entry(
                hs, line.local_code,
                line.description_cn or "", line.description_en or "",
                _make_ruling_list(match_rulings), tariff,
            ))

    # Sort: pre-ruling matches (ranked by match count) first, then tariff line matches, then by MFN rate
    results.sort(key=lambda x: (
        0 if x["matched_rulings"] else 1,
        -len(x["matched_rulings"]) if x["matched_rulings"] else 0,
        -(x["mfn_rate"] or 0) if x["mfn_rate"] else 0,
    ))

    return {
        "product_name": body.product_name,
        "dest_country": body.dest_country,
        "recommendations": results[:15],
    }


@router.post("/enterprise/classify")
def enterprise_classify(
    body: EnterpriseClassifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_user(["admin", "customs_mgr", "customs_staff", "compliance"])),
):
    """关务确认 HS 编码并保存归类记录"""
    if not body.hs_code_candidate:
        raise HTTPException(400, "请先选择 HS 编码")

    tariff = lookup_tariff(db, body.hs_code_candidate, body.dest_country, "CN")

    record = create_classification(db, {
        "classified_hs_code": body.hs_code_candidate,
        "product_name_cn": body.product_name,
        "product_name_en": body.product_name,
        "product_description": body.product_description,
        "brand": body.brand,
        "model": body.model,
        "specifications": body.specifications,
        "material_composition": body.material_composition,
        "function_description": body.function_description,
        "use_purpose": body.use_purpose,
        "classification_basis": "SELF_CLASSIFY",
        "confidence_level": "MEDIUM",
        "classified_by": getattr(current_user, "display_name", None) or getattr(current_user, "username", "unknown"),
    })

    return {
        "id": record.id,
        "hs_code": body.hs_code_candidate,
        "product_name": body.product_name,
        "status": record.status,
        "tariff_rates": {
            "mfn_rate": float(tariff.get("mfn_rate", 0)) if tariff and tariff.get("mfn_rate") else None,
            "fta_rates": [
                {"agreement": f.get("agreement"), "rate_pct": float(f.get("rate_pct", 0))}
                for f in (tariff.get("fta_rates", []) if tariff else [])
            ] if tariff else [],
            "additional_duties": tariff.get("additional_duties", []) if tariff else [],
            "total_effective_rate": float(tariff.get("total_effective_rate", 0)) if tariff else None,
        } if tariff else {},
        "created_at": str(datetime.now()),
    }


@router.get("/search")
@router.get("/lookup")
def lookup_classification(
    product_code: Optional[str] = None,
    hs_code: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return get_classification(db, product_code=product_code, hs_code=hs_code,
                              brand=brand, model=model)


@router.get("/rulings")
def rulings_search(
    query: Optional[str] = None,
    hs_code: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    return search_rulings(db, query=query, hs_code=hs_code,
                          country=country, limit=limit)


@router.get("/history")
def classification_history(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_classification(db, limit=limit)


@router.get("/consistency-check")
def consistency_check(
    product_code: str = Query(...),
    db: Session = Depends(get_db),
):
    return check_consistency(db, product_code)
