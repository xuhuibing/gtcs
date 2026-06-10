from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal


class CostScenario(BaseModel):
    origin: str
    fob: Decimal
    freight: Decimal = Decimal("0")
    insurance: Decimal = Decimal("0")


class CostSimulateRequest(BaseModel):
    hs_code: str
    dest_country: str
    scenarios: List[CostScenario]


class CostResult(BaseModel):
    origin: str
    fob: Decimal
    freight: Decimal
    insurance: Decimal
    cif: Decimal
    mfn_rate: Optional[Decimal] = None
    fta_rate: Optional[Decimal] = None
    fta_name: Optional[str] = None
    additional_duty_rate: Decimal = Decimal("0")
    additional_duty_type: Optional[str] = None
    total_rate: Decimal
    duty_amount: Decimal
    landed_cost: Decimal


class CostSimulateResponse(BaseModel):
    hs_code: str
    dest_country: str
    comparisons: List[CostResult]
    recommendation: Optional[str] = None
    saving_vs_cn: Optional[Decimal] = None


# ─── 企业级成本模拟 v2 ───

class EnterpriseOriginInput(BaseModel):
    origin_country: str = "CN"
    freight: Decimal = Decimal("0")
    insurance: Decimal = Decimal("0")


class EnterpriseSimulateRequest(BaseModel):
    product_name: str = ""
    product_description: str = ""
    hs_code: Optional[str] = None
    dest_country: str = "VN"
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    currency: str = "USD"
    incoterm: str = "CIF"
    origins: List[EnterpriseOriginInput] = [EnterpriseOriginInput()]


class EnterpriseSimulateResponse(BaseModel):
    status: str = "success"
    hs_code_determined: str = ""
    hs_description: str = ""
    product_name: str = ""
    dest_country: str = ""
    dest_name: str = ""
    quantity: int = 0
    unit_price: float = 0
    currency: str = "USD"
    incoterm: str = ""
    incoterm_description: str = ""
    vat_config: Dict[str, Any] = {}
    certification_requirements: List[Dict[str, Any]] = []
    comparisons: List[Dict[str, Any]] = []
    recommendation: Optional[Dict[str, Any]] = None
