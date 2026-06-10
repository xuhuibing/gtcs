from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.product import Product, HSMapping
from app.models.compliance import HSClassificationRecord

router = APIRouter(prefix="/product", tags=["商品管理"])


class ProductIn(BaseModel):
    enterprise_id: int
    product_code: str
    name_cn: str
    name_en: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[str] = None
    unit: str = "PCS"
    unit_price: Optional[float] = None
    currency: str = "USD"


class HSMappingIn(BaseModel):
    product_id: int
    country: str
    hs_code: str
    description_local: Optional[str] = None
    declaration_elements: Optional[str] = None
    is_primary: int = 0


@router.get("/list")
@router.get("/")
def list_products(
    enterprise_id: Optional[int] = None,
    query: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if enterprise_id:
        q = q.filter(Product.enterprise_id == enterprise_id)
    if query:
        q = q.filter(
            Product.product_code.ilike(f"%{query}%") |
            Product.name_cn.ilike(f"%{query}%") |
            Product.name_en.ilike(f"%{query}%")
        )
    products = q.limit(limit).all()
    return [{
        "id": p.id,
        "product_code": p.product_code,
        "name_cn": p.name_cn,
        "name_en": p.name_en,
        "brand": p.brand,
        "model": p.model,
        "unit": p.unit,
    } for p in products]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    hs_mappings = db.query(HSMapping).filter(HSMapping.product_id == product_id).all()
    classifications = db.query(HSClassificationRecord).filter(
        HSClassificationRecord.product_code == p.product_code,
        HSClassificationRecord.status == "ACTIVE",
    ).order_by(HSClassificationRecord.id.desc()).limit(10).all()
    return {
        "id": p.id,
        "enterprise_id": p.enterprise_id,
        "product_code": p.product_code,
        "name_cn": p.name_cn,
        "name_en": p.name_en,
        "brand": p.brand,
        "model": p.model,
        "specifications": p.specifications,
        "unit": p.unit,
        "unit_price": p.unit_price,
        "currency": p.currency,
        "hs_mappings": [{"id": m.id, "country": m.country, "hs_code": m.hs_code, "is_primary": m.is_primary} for m in hs_mappings],
        "classifications": [{"id": c.id, "classified_hs_code": c.classified_hs_code, "confidence_level": c.confidence_level, "classified_by": c.classified_by} for c in classifications],
    }


@router.post("/create")
@router.post("/")
def create_product(body: ProductIn, db: Session = Depends(get_db)):
    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "product_code": product.product_code, "name_cn": product.name_cn}


@router.post("/hs-mapping")
def create_hs_mapping(body: HSMappingIn, db: Session = Depends(get_db)):
    mapping = HSMapping(**body.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return {"id": mapping.id, "country": mapping.country, "hs_code": mapping.hs_code}
