"""原产地规则引擎 — RVC计算 + CTC判定 + FTA资格评估

支持三种 RVC 计算方法:
  - BUILD_DOWN: RVC = (EXW - VNM) / EXW × 100%
  - BUILD_UP:   RVC = (VOM + L) / EXW × 100%
  - NET_COST:   RVC = (NC - VNM) / NC × 100%

CTC (关税税号变更) 判定:
  - CC (章级变更): 前2位不同
  - CTH (品目级变更): 前4位不同
  - CTSH (子目级变更): 前6位不同
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.origin import (
    OriginProfile, OriginBOMDetail, OriginProcessStep,
    OriginCostBreakdown, OriginCertificate, RulesOfOrigin,
    OriginAssessment,
)
from app.models.tariff import TradeAgreement


# ─── RVC Calculator ────────────────────────────────────

def calc_rvc_build_down(exw: Decimal, vnm: Decimal) -> Decimal:
    """扣减法 (Build-down): RVC = (EXW - VNM) / EXW × 100%

    EXW = 出厂价 (Ex-works price)
    VNM = 非原产材料价值 (Value of non-originating materials)
    """
    if not exw or exw <= 0:
        return Decimal("0")
    return ((exw - vnm) / exw * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calc_rvc_build_up(vom: Decimal, labor: Decimal, overhead: Decimal, exw: Decimal) -> Decimal:
    """累加法 (Build-up): RVC = (VOM + L + OH) / EXW × 100%

    VOM = 原产材料价值 (Value of originating materials)
    L = 直接人工成本 (Direct labor)
    OH = 制造费用 (Manufacturing overhead)
    """
    if not exw or exw <= 0:
        return Decimal("0")
    return ((vom + labor + overhead) / exw * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calc_rvc_net_cost(nc: Decimal, vnm: Decimal) -> Decimal:
    """净成本法 (Net Cost): RVC = (NC - VNM) / NC × 100%

    NC = 净成本 (总成本扣除营销/运输/售后)
    """
    if not nc or nc <= 0:
        return Decimal("0")
    return ((nc - vnm) / nc * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ─── CTC Checker ───────────────────────────────────────

def check_ctc(hs_code: str, material_hs_code: str, level: str = "CTH") -> bool:
    """检查HS编码是否发生指定级别的税则改变。

    Args:
        hs_code: 成品HS编码 (不含点)
        material_hs_code: 原料HS编码 (不含点)
        level: CC(2位) / CTH(4位) / CTSH(6位)

    Returns:
        True if tariff shift occurred at the specified level
    """
    hs = hs_code.replace(".", "").replace(" ", "")
    mat = material_hs_code.replace(".", "").replace(" ", "")

    if level == "CC":
        return hs[:2] != mat[:2]
    elif level == "CTH":
        return hs[:4] != mat[:4]
    elif level == "CTSH":
        return hs[:6] != mat[:6]
    else:
        raise ValueError(f"Unknown CTC level: {level} (use CC/CTH/CTSH)")


def check_ctc_from_bom(profile_id: int, level: str, db: Session) -> Dict[str, Any]:
    """基于BOM明细检查所有非原产料件是否满足CTC要求。"""
    bom_items = db.query(OriginBOMDetail).filter(
        OriginBOMDetail.profile_id == profile_id,
        OriginBOMDetail.is_originating == False,
    ).all()

    profile = db.query(OriginProfile).filter(OriginProfile.id == profile_id).first()
    if not profile or not bom_items:
        return {"cth_met": False, "details": [], "non_originating_count": len(bom_items)}

    results = []
    all_met = True
    for item in bom_items:
        if item.material_hs_code and profile.hs_code:
            shifted = check_ctc(profile.hs_code, item.material_hs_code, level)
            results.append({
                "material_code": item.material_code,
                "material_name": item.material_name,
                "product_hs": profile.hs_code,
                "material_hs": item.material_hs_code,
                "shifted": shifted,
                "tariff_shift_from": item.tariff_shift_from,
                "tariff_shift_to": item.tariff_shift_to,
            })
            if not shifted:
                all_met = False

    return {
        "cth_met": all_met,
        "level": level,
        "details": results,
        "non_originating_count": len(bom_items),
    }


# ─── Qualification Assessment ──────────────────────────

def assess_fta_qualification(
    db: Session, profile_id: int, agreement_code: str
) -> Dict[str, Any]:
    """评估产品是否满足特定FTA的原产地资格。"""
    profile = db.query(OriginProfile).filter(OriginProfile.id == profile_id).first()
    agreement = db.query(TradeAgreement).filter(TradeAgreement.code == agreement_code).first()
    if not profile or not agreement:
        return {"qualified": False, "reason": "Profile or agreement not found"}

    # Get ROO rules for this HS code
    hs_prefix = profile.hs_code[:4]  # Get heading level
    roo_rules = db.query(RulesOfOrigin).filter(
        RulesOfOrigin.agreement_id == agreement.id,
        RulesOfOrigin.hs_code.like(f"{hs_prefix}%"),
    ).all()

    rvc_met = None
    ctc_met = None
    method_used = None
    reasons = []

    # Check if RVC rule applies
    rvc_threshold = Decimal("0")
    for rule in roo_rules:
        if rule.criteria_type == "RVC":
            try:
                rvc_threshold = Decimal(rule.threshold_value.replace("%", "").strip())
            except (ValueError, AttributeError):
                rvc_threshold = Decimal("40")  # default

            if profile.rvc_calculated is not None:
                rvc_met = Decimal(str(profile.rvc_calculated)) >= rvc_threshold
                method_used = profile.rvc_method or "BUILD_DOWN"
                reasons.append(
                    f"RVC {profile.rvc_calculated}% ≥ {rvc_threshold}% threshold"
                    if rvc_met else
                    f"RVC {profile.rvc_calculated}% < {rvc_threshold}% threshold"
                )

        elif rule.criteria_type == "CTC":
            bom_check = check_ctc_from_bom(profile_id, rule.threshold_value or "CTH", db)
            ctc_met = bom_check["cth_met"]
            reasons.append(
                f"CTC({rule.threshold_value}) {'met' if ctc_met else 'not met'}"
            )

    # Determine qualification
    if rvc_met and ctc_met is not False:
        qualified = rvc_met
        method_used = "RVC"
    elif ctc_met:
        qualified = True
        method_used = "CTC"
    elif rvc_met and ctc_met is None:
        qualified = True
        method_used = "RVC"
    else:
        qualified = False
        method_used = method_used or "N/A"

    return {
        "qualified": qualified,
        "agreement_code": agreement_code,
        "agreement_name": agreement.name_en,
        "method_used": method_used,
        "rvc_met": rvc_met,
        "rvc_calculated": float(profile.rvc_calculated) if profile.rvc_calculated else None,
        "rvc_threshold": float(rvc_threshold) if rvc_threshold else None,
        "ctc_met": ctc_met,
        "reasons": reasons,
    }


def assess_all_agreements(db: Session, profile_id: int) -> List[Dict[str, Any]]:
    """评估产品在指定制造地的所有适用FTA资格。"""
    profile = db.query(OriginProfile).filter(OriginProfile.id == profile_id).first()
    if not profile:
        return []

    qualifying_countries = {profile.manufacturing_country}

    agreements = db.query(TradeAgreement).filter(
        TradeAgreement.member_countries.contains(profile.manufacturing_country)
    ).all()

    results = []
    for agreement in agreements:
        result = assess_fta_qualification(db, profile_id, agreement.code)
        results.append(result)

    # Sort by qualified first, then by name
    results.sort(key=lambda x: (not x["qualified"], x["agreement_code"]))
    return results


# ─── RVC Assessment from Profile Data ──────────────────

def update_rvc_from_bom(db: Session, profile_id: int) -> Dict[str, Any]:
    """从BOM数据重新计算RVC并更新profile。"""
    profile = db.query(OriginProfile).filter(OriginProfile.id == profile_id).first()
    if not profile:
        return {"error": "Profile not found"}

    bom_items = db.query(OriginBOMDetail).filter(
        OriginBOMDetail.profile_id == profile_id
    ).all()

    if not bom_items:
        return {"error": "No BOM items found"}

    # Calculate material costs
    total_material = sum((Decimal(str(i.total_cost or 0)) for i in bom_items), Decimal("0"))
    local_material = sum(
        (Decimal(str(i.total_cost or 0)) for i in bom_items if i.is_local or i.is_originating),
        Decimal("0"),
    )
    imported_material = sum(
        (Decimal(str(i.total_cost or 0)) for i in bom_items if not (i.is_local or i.is_originating)),
        Decimal("0"),
    )

    labor = profile.labor_cost or Decimal("0")
    overhead = profile.overhead_cost or Decimal("0")
    exw = profile.ex_works_price or Decimal("0")

    # Build-down RVC
    rvc_val = calc_rvc_build_down(exw, imported_material)

    # Update profile
    profile.total_material_cost = total_material
    profile.local_material_cost = local_material
    profile.imported_material_cost = imported_material
    profile.rvc_calculated = rvc_val
    profile.rvc_method = "BUILD_DOWN"

    # Determine threshold from the first applicable agreement
    agreements = db.query(TradeAgreement).filter(
        TradeAgreement.member_countries.contains(profile.manufacturing_country)
    ).all()
    for agreement in agreements:
        rules = db.query(RulesOfOrigin).filter(
            RulesOfOrigin.agreement_id == agreement.id,
            RulesOfOrigin.criteria_type == "RVC",
        ).first()
        if rules:
            try:
                threshold = Decimal(rules.threshold_value.replace("%", "").strip())
                profile.rvc_threshold = threshold
                break
            except (ValueError, AttributeError):
                pass
    if profile.rvc_threshold is None:
        profile.rvc_threshold = Decimal("40")

    db.commit()

    return {
        "profile_id": profile_id,
        "rvc_calculated": float(rvc_val),
        "rvc_method": "BUILD_DOWN",
        "rvc_threshold": float(profile.rvc_threshold),
        "total_material_cost": float(total_material),
        "local_material_cost": float(local_material),
        "imported_material_cost": float(imported_material),
        "labor_cost": float(labor),
        "overhead": float(overhead),
        "ex_works_price": float(exw),
    }


def run_full_assessment(db: Session, profile_id: int) -> Dict[str, Any]:
    """对指定profile运行完整原产地评估。"""
    # 1. Update RVC from BOM
    rvc_result = update_rvc_from_bom(db, profile_id)

    if "error" in rvc_result:
        return rvc_result

    # 2. Assess all applicable agreements
    agreement_results = assess_all_agreements(db, profile_id)

    # 3. Determine overall origin status
    qualified_agreements = [r for r in agreement_results if r["qualified"]]
    if qualified_agreements:
        origin_status = "QUALIFIES"
        best_agreement = qualified_agreements[0]["agreement_code"]
    else:
        origin_status = "DOES_NOT_QUALIFY"
        best_agreement = None

    # 4. Update profile
    profile = db.query(OriginProfile).filter(OriginProfile.id == profile_id).first()
    if profile:
        profile.origin_status = origin_status
        profile.target_agreement = best_agreement
        db.commit()

    return {
        "profile_id": profile_id,
        "product_code": profile.product_code if profile else None,
        "origin_status": origin_status,
        "best_agreement": best_agreement,
        "rvc": rvc_result,
        "agreements": agreement_results,
    }
