from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.cost import CostSimulateRequest, CostSimulateResponse, EnterpriseSimulateRequest, EnterpriseSimulateResponse
from app.services.cost_simulator import simulate_cost
from app.services.enterprise_cost_simulator import enterprise_simulate
from app.services.vat_service import get_vat_config
from app.services.compliance_service import get_import_requirements

router = APIRouter(prefix="/cost", tags=["Cost Simulation"])


@router.post("/simulate", response_model=CostSimulateResponse)
def cost_simulate(req: CostSimulateRequest, db: Session = Depends(get_db)):
    scenarios = [s.model_dump() for s in req.scenarios]
    result = simulate_cost(db, req.hs_code, req.dest_country, scenarios)
    return result


@router.post("/enterprise-simulate", response_model=EnterpriseSimulateResponse)
def enterprise_cost_simulate(req: EnterpriseSimulateRequest, db: Session = Depends(get_db)):
    """企业级进口成本模拟 — 承接上游需求，输出关务分析"""
    return enterprise_simulate(
        db,
        product_name=req.product_name,
        product_description=req.product_description,
        hs_code=req.hs_code or "",
        dest_country=req.dest_country,
        quantity=req.quantity,
        unit_price=req.unit_price,
        currency=req.currency,
        incoterm=req.incoterm,
        origins=[o.model_dump() for o in req.origins],
    )


@router.get("/vat-config")
def vat_config(dest_country: str = Query(..., description="目的国 ISO2 代码")):
    """获取目的国 VAT/GST 配置"""
    return get_vat_config(dest_country)


@router.get("/requirements")
def import_requirements(
    dest_country: str = Query(...),
    hs_code: str = Query("", description="HS 编码前2-6位"),
):
    """获取目的国对特定 HS 编码的认证要求"""
    return get_import_requirements(dest_country, hs_code)
