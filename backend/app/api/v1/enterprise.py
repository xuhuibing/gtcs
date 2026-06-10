from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.enterprise import Enterprise, Factory, Supplier, License

router = APIRouter(prefix="/enterprise", tags=["企业管理"])


class EnterpriseIn(BaseModel):
    name_cn: str
    name_en: Optional[str] = None
    credit_code: Optional[str] = None
    customs_code: Optional[str] = None
    aeo_level: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None


@router.get("/list")
@router.get("/")
def list_enterprises(limit: int = 20, db: Session = Depends(get_db)):
    enterprises = db.query(Enterprise).limit(limit).all()
    return [{
        "id": e.id,
        "name_cn": e.name_cn,
        "name_en": e.name_en,
        "credit_code": e.credit_code,
        "customs_code": e.customs_code,
        "aeo_level": e.aeo_level,
        "contact_person": e.contact_person,
    } for e in enterprises]


@router.get("/{enterprise_id}")
def get_enterprise(enterprise_id: int, db: Session = Depends(get_db)):
    e = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="企业不存在")
    factories = db.query(Factory).filter(Factory.enterprise_id == enterprise_id).all()
    suppliers = db.query(Supplier).filter(Supplier.enterprise_id == enterprise_id).all()
    licenses = db.query(License).filter(License.enterprise_id == enterprise_id).all()
    return {
        "id": e.id,
        "name_cn": e.name_cn,
        "name_en": e.name_en,
        "credit_code": e.credit_code,
        "customs_code": e.customs_code,
        "aeo_level": e.aeo_level,
        "address": e.address,
        "contact_person": e.contact_person,
        "contact_phone": e.contact_phone,
        "factories": [{"id": f.id, "name": f.name, "country": f.country, "is_primary": f.is_primary} for f in factories],
        "suppliers": [{"id": s.id, "name": s.name, "country": s.country, "risk_level": s.risk_level} for s in suppliers],
        "licenses": [{"id": l.id, "license_type": l.license_type, "license_no": l.license_no, "status": l.status} for l in licenses],
    }


@router.post("/create")
@router.post("/")
def create_enterprise(body: EnterpriseIn, db: Session = Depends(get_db)):
    ent = Enterprise(**body.model_dump())
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return {"id": ent.id, "name_cn": ent.name_cn}


@router.put("/{enterprise_id}")
def update_enterprise(enterprise_id: int, body: EnterpriseIn, db: Session = Depends(get_db)):
    e = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="企业不存在")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(e, key, val)
    db.commit()
    return {"id": e.id, "name_cn": e.name_cn}
