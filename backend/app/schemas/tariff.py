from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal


class TariffLookupRequest(BaseModel):
    hs_code: str
    dest_country: str
    origin_country: str = "CN"
    value_usd: Optional[Decimal] = None


class TariffRateItem(BaseModel):
    rate_type: str
    rate_pct: Optional[Decimal]
    agreement: Optional[str] = None
    origin_scope: Optional[str] = None


class AdditionalDutyItem(BaseModel):
    duty_type: str
    rate_pct: Decimal
    legal_basis: Optional[str] = None
    target_origin: Optional[str] = None


class TariffLookupResponse(BaseModel):
    hs_code: str
    country: str
    origin_country: str
    local_code: Optional[str] = None
    description: Optional[str] = None
    description_cn: Optional[str] = None
    unit: Optional[str] = None
    mfn_rate: Optional[Decimal] = None
    column2_rate: Optional[Decimal] = None
    fta_rates: List[TariffRateItem] = []
    additional_duties: List[AdditionalDutyItem] = []
    total_additional_rate: Optional[Decimal] = None
    total_effective_rate: Optional[Decimal] = None
    estimated_duty: Optional[Decimal] = None


class TariffCompareRequest(BaseModel):
    hs_code: str
    dest_country: str
    origins: List[str] = ["CN", "VN", "TH"]


class TariffCompareItem(BaseModel):
    origin: str
    mfn_rate: Optional[Decimal] = None
    best_fta_rate: Optional[Decimal] = None
    best_fta_name: Optional[str] = None
    additional_duty_rate: Decimal = Decimal("0")
    total_rate: Optional[Decimal] = None


class TariffCompareResponse(BaseModel):
    hs_code: str
    dest_country: str
    comparisons: List[TariffCompareItem]
    recommended_origin: Optional[str] = None


class HSSearchResult(BaseModel):
    local_code: str
    description_en: Optional[str] = None
    description_cn: Optional[str] = None
    country: str
