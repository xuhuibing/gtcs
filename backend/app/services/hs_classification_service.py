from __future__ import annotations
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.compliance import HSClassificationRecord, HSRulingReference
from app.services.tariff_service import get_country_id


def create_classification(db: Session, data: dict) -> HSClassificationRecord:
    record = HSClassificationRecord(
        product_code=data.get("product_code"),
        product_name_cn=data.get("product_name_cn"),
        product_name_en=data.get("product_name_en"),
        product_description=data.get("product_description"),
        brand=data.get("brand"),
        model=data.get("model"),
        specifications=data.get("specifications"),
        material_composition=data.get("material_composition"),
        function_description=data.get("function_description"),
        use_purpose=data.get("use_purpose"),
        classified_hs_code=data["classified_hs_code"],
        classified_country_id=data.get("classified_country_id"),
        classification_basis=data.get("classification_basis", "SELF_CLASSIFY"),
        confidence_level=data.get("confidence_level", "MEDIUM"),
        ruling_number=data.get("ruling_number"),
        ruling_country=data.get("ruling_country"),
        ruling_date=data.get("ruling_date"),
        ruling_hs_code=data.get("ruling_hs_code"),
        ruling_product_description=data.get("ruling_product_description"),
        ruling_key_reasoning=data.get("ruling_key_reasoning"),
        ruling_source_url=data.get("ruling_source_url"),
        classification_notes=data.get("classification_notes"),
        key_classification_factors=data.get("key_classification_factors"),
        alternative_hs_codes=data.get("alternative_hs_codes"),
        rejection_reasons=data.get("rejection_reasons"),
        classified_by=data.get("classified_by"),
        reviewed_by=data.get("reviewed_by"),
        valid_from=data.get("valid_from"),
        valid_to=data.get("valid_to"),
        status="ACTIVE",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_classification(db: Session, product_code: str = None,
                       hs_code: str = None, brand: str = None,
                       model: str = None, limit: int = 50) -> List[dict]:
    q = db.query(HSClassificationRecord).filter(HSClassificationRecord.status == "ACTIVE")

    if product_code:
        q = q.filter(HSClassificationRecord.product_code == product_code)
    if hs_code:
        clean = hs_code.replace(".", "").replace(" ", "")
        q = q.filter(HSClassificationRecord.classified_hs_code.like(f"{clean}%"))
    if brand:
        q = q.filter(HSClassificationRecord.brand == brand)
    if model:
        q = q.filter(HSClassificationRecord.model == model)

    records = q.order_by(desc(HSClassificationRecord.created_at)).limit(limit).all()

    return [{
        "id": r.id,
        "product_code": r.product_code,
        "product_name_cn": r.product_name_cn,
        "product_name_en": r.product_name_en,
        "brand": r.brand,
        "model": r.model,
        "classified_hs_code": r.classified_hs_code,
        "classification_basis": r.classification_basis,
        "confidence_level": r.confidence_level,
        "key_classification_factors": r.key_classification_factors,
        "alternative_hs_codes": r.alternative_hs_codes,
        "ruling_number": r.ruling_number,
        "status": r.status,
        "classified_by": r.classified_by,
        "valid_from": str(r.valid_from) if r.valid_from else None,
        "valid_to": str(r.valid_to) if r.valid_to else None,
    } for r in records]


def search_rulings(db: Session, query: str = None, hs_code: str = None,
                   country: str = None, limit: int = 30) -> List[dict]:
    q = db.query(HSRulingReference)

    if hs_code:
        clean = hs_code.replace(".", "").replace(" ", "")
        q = q.filter(HSRulingReference.hs_code.like(f"{clean}%"))
    if query:
        q = q.filter(or_(
            HSRulingReference.product_name.ilike(f"%{query}%"),
            HSRulingReference.product_description.ilike(f"%{query}%"),
            HSRulingReference.classification_reasoning.ilike(f"%{query}%"),
        ))
    if country:
        cid = get_country_id(db, country)
        if cid:
            q = q.filter(HSRulingReference.country_id == cid)

    rulings = q.order_by(desc(HSRulingReference.ruling_date)).limit(limit).all()

    return [{
        "id": r.id,
        "ruling_number": r.ruling_number,
        "ruling_type": r.ruling_type,
        "ruling_date": str(r.ruling_date) if r.ruling_date else None,
        "hs_code": r.hs_code,
        "product_name": r.product_name,
        "product_description": r.product_description,
        "classification_reasoning": r.classification_reasoning,
        "key_factors": r.key_factors,
        "source_url": r.source_url,
    } for r in rulings]


def check_consistency(db: Session, product_code: str) -> dict:
    records = db.query(HSClassificationRecord).filter(
        HSClassificationRecord.product_code == product_code,
        HSClassificationRecord.status == "ACTIVE",
    ).all()

    if not records:
        return {"product_code": product_code, "status": "NOT_FOUND", "records": []}

    hs_codes = set(r.classified_hs_code for r in records)
    countries = set(r.classified_country_id for r in records)

    inconsistent = len(hs_codes) > 1 and len(countries) == 1

    return {
        "product_code": product_code,
        "status": "INCONSISTENT" if inconsistent else "CONSISTENT",
        "unique_hs_codes": list(hs_codes),
        "record_count": len(records),
        "warning": "同一产品在同一国家存在多个不同HS归类" if inconsistent else None,
        "records": [{
            "id": r.id,
            "classified_hs_code": r.classified_hs_code,
            "classification_basis": r.classification_basis,
            "confidence_level": r.confidence_level,
            "classified_by": r.classified_by,
        } for r in records],
    }
