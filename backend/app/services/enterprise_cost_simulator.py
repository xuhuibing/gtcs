"""企业级进口成本模拟编排服务"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.services.tariff_service import lookup_tariff
from app.services.vat_service import get_vat_config, calculate_vat
from app.services.compliance_service import get_import_requirements
from app.models.country_hs import Country
from app.models.tariff import NationalTariffLine


INCOTERMS = {
    "EXW": "工厂交货 Ex Works",
    "FOB": "离岸价 Free on Board",
    "CIF": "到岸价 Cost, Insurance & Freight",
    "DAP": "目的地交货 Delivered at Place",
    "DDP": "完税后交货 Delivered Duty Paid",
    "CPT": "运费付至 Carriage Paid To",
}


def enterprise_simulate(
    db: Session,
    product_name: str = "",
    product_description: str = "",
    hs_code: str = "",
    dest_country: str = "VN",
    quantity: int = 1,
    unit_price: Decimal = Decimal("0"),
    currency: str = "USD",
    incoterm: str = "CIF",
    origins: Optional[list] = None,
) -> dict:
    """企业级进口成本模拟

    1. HS 确认 —— 提供则验证，不提供则搜索兜底
    2. 获取目的国信息、VAT 配置、认证要求
    3. 对每个原产国计算：关税 → VAT → 总到岸成本
    """
    if origins is None:
        origins = [{"origin_country": "CN", "freight": Decimal("0"), "insurance": Decimal("0")}]

    for o in origins:
        if isinstance(o.get("freight"), (int, float)):
            o["freight"] = Decimal(str(o["freight"]))
        if isinstance(o.get("insurance"), (int, float)):
            o["insurance"] = Decimal(str(o["insurance"]))

    # 1. HS 确认
    hs_determined = hs_code
    hs_description = ""
    if hs_determined:
        line = db.query(NationalTariffLine).filter(
            NationalTariffLine.local_code.like(f"{hs_determined.replace('.', '').replace(' ', '')}%")
        ).first()
        if line:
            hs_description = line.description_cn or line.description_en or ""
        else:
            # 如果没有精确匹配，尝试搜索
            pass

    # 如果没有提供 HS 或未匹配到，搜索
    if not hs_determined or not hs_description:
        matches = db.query(NationalTariffLine).filter(
            NationalTariffLine.description_en.ilike(f"%{product_name}%")
        ).limit(1).all()
        if not matches:
            matches = db.query(NationalTariffLine).filter(
                NationalTariffLine.description_cn.ilike(f"%{product_name}%")
            ).limit(1).all()
        if matches:
            hs_determined = matches[0].local_code
            hs_description = matches[0].description_cn or matches[0].description_en or ""

    dest_name = db.query(Country.name_cn).filter(Country.iso2 == dest_country).scalar() or dest_country

    # 2. VAT + 认证
    vat_cfg = get_vat_config(dest_country)
    certs = get_import_requirements(dest_country, hs_determined)

    # 3. 计算每个原产国的成本
    comparisons = []
    for origin in origins:
        oc = origin.get("origin_country", "CN")
        freight = Decimal(str(origin.get("freight", "0")))
        insurance = Decimal(str(origin.get("insurance", "0")))

        fob_total = Decimal(str(unit_price)) * Decimal(str(quantity))
        cif_value = fob_total + freight + insurance

        # 查询关税
        tariff_data = lookup_tariff(db, hs_determined, dest_country, oc)
        if tariff_data is None:
            tariff_data = {}

        mfn_rate = tariff_data.get("mfn_rate") or Decimal("0")
        column2_rate = tariff_data.get("column2_rate")
        fta_rates = tariff_data.get("fta_rates", [])
        additional_duties = tariff_data.get("additional_duties", [])
        total_additional = tariff_data.get("total_additional_rate") or Decimal("0")

        # 选择最优税率
        fta_info = None
        best_rate = mfn_rate
        for fr in fta_rates:
            r = fr.get("rate_pct")
            if r is not None and r < best_rate:
                best_rate = r
                fta_info = fr

        # 附加税
        additional_rate = total_additional
        if isinstance(additional_rate, (int, float)):
            additional_rate = Decimal(str(additional_rate))

        selected_rate = best_rate + additional_rate
        duty_amount = cif_value * selected_rate / Decimal("100")

        # VAT
        vat_result = calculate_vat(cif_value, duty_amount, dest_country)

        total_landed = cif_value + duty_amount + vat_result["amount"]

        # 成本分解
        components = [
            {"component": "fob", "label": "FOB 货值", "amount": fob_total},
            {"component": "freight", "label": "运费", "amount": freight},
            {"component": "insurance", "label": "保险费", "amount": insurance},
            {"component": "duty", "label": "关税", "amount": duty_amount},
            {"component": "vat", "label": f"VAT ({vat_result['rate_pct']})", "amount": vat_result["amount"]},
        ]
        breakdown = []
        for c in components:
            pct = float(c["amount"]) / float(total_landed) * 100 if total_landed else 0
            breakdown.append({
                "component": c["component"],
                "label": c["label"],
                "amount": float(c["amount"].quantize(Decimal("0.01"))),
                "pct": round(pct, 2),
            })

        origin_name = db.query(Country.name_cn).filter(Country.iso2 == oc).scalar() or oc
        tariff_detail = {
            "mfn_rate_pct": f"{float(mfn_rate):.2f}%",
            "column2_rate_pct": f"{float(column2_rate):.2f}%" if column2_rate is not None else None,
            "fta_rate": {
                "available": fta_info is not None,
                "rate_pct": f"{float(fta_info['rate_pct']):.2f}%" if fta_info else None,
                "agreement": fta_info.get("agreement") if fta_info else None,
            } if fta_info else None,
            "additional_rate_pct": f"{float(additional_rate):.2f}%",
            "selected_rate_pct": f"{float(selected_rate):.2f}%",
            "duty_amount": float(duty_amount.quantize(Decimal("0.01"))),
            "saving_vs_mfn": float((cif_value * (mfn_rate + additional_rate) / Decimal("100") - duty_amount).quantize(Decimal("0.01"))),
        }

        comparisons.append({
            "origin_country": oc,
            "origin_name": origin_name,
            "unit_price": float(unit_price),
            "quantity": quantity,
            "fob_total": float(fob_total.quantize(Decimal("0.01"))),
            "freight": float(freight.quantize(Decimal("0.01"))),
            "insurance": float(insurance.quantize(Decimal("0.01"))),
            "cif_value": float(cif_value.quantize(Decimal("0.01"))),
            "tariff": tariff_detail,
            "vat": {
                "tax_type": vat_result["tax_type"],
                "tax_name": vat_result["tax_name"],
                "rate_pct": vat_result["rate_pct"],
                "taxable_base": float(vat_result["taxable_base"]),
                "amount": float(vat_result["amount"]),
            },
            "total_landed_cost": float(total_landed.quantize(Decimal("0.01"))),
            "cost_breakdown": breakdown,
        })

    # 排序：总到岸成本升序
    comparisons.sort(key=lambda x: x["total_landed_cost"])
    recommendation = comparisons[0]["origin_country"] if comparisons else None

    return {
        "status": "success",
        "hs_code_determined": hs_determined,
        "hs_description": hs_description,
        "product_name": product_name,
        "dest_country": dest_country,
        "dest_name": dest_name,
        "quantity": quantity,
        "unit_price": float(unit_price),
        "currency": currency,
        "incoterm": incoterm,
        "incoterm_description": INCOTERMS.get(incoterm, incoterm),
        "vat_config": {
            "tax_type": vat_cfg["tax_type"],
            "tax_name": vat_cfg["tax_name"],
            "rate_pct": vat_cfg["rate_pct"],
            "notes": vat_cfg["notes"],
        },
        "certification_requirements": certs,
        "comparisons": comparisons,
        "recommendation": {
            "best_origin": recommendation,
            "best_landed_cost": comparisons[0]["total_landed_cost"] if comparisons else 0,
            "total_saving": round(comparisons[-1]["total_landed_cost"] - comparisons[0]["total_landed_cost"], 2) if len(comparisons) > 1 else 0,
        } if recommendation else None,
    }
