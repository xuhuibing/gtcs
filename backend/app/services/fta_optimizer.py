from __future__ import annotations
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.tariff_service import lookup_tariff


CERTIFICATE_MAP = {
    "RCEP": "RCEP原产地证(自主声明或官方签发)",
    "ACFTA": "Form E (中国-东盟原产地证)",
    "CPTPP": "CPTPP原产地声明",
    "USMCA": "USMCA Certificate of Origin",
    "EVFTA": "EUR.1 或 REX自主声明",
    "EU_GSP": "Form A / REX注册声明",
    "AIFTA": "Form AI (东盟-印度)",
    "KAFTA": "Form AK (韩国-东盟)",
}

ROO_NOTES = {
    "RCEP": "RVC≥40% 或 CTH(税目改变) — 可累积区域内成员国材料价值",
    "ACFTA": "RVC≥40% 或 CTH — 可使用东盟累积规则",
    "CPTPP": "RVC≥45% (扣减法) 或 35% (累加法) — 纱线前后工序规则适用纺织品",
    "USMCA": "RVC≥75%(汽车)/60%(其他) — 劳动价值含量(LVC)适用汽车",
    "EVFTA": "产品特定规则(PSR) — 多数电子品: MaxNOM 50% EXW 或 CTH",
}


def recommend_fta(db: Session, hs_code: str, origin: str, dest: str):
    tariff_data = lookup_tariff(db, hs_code, dest, origin)
    if not tariff_data:
        return {"available_agreements": [], "best_option": None, "notes": "No tariff data found"}

    options = []

    mfn_rate = tariff_data.get("mfn_rate") or Decimal("0")
    options.append({
        "code": "MFN",
        "rate": mfn_rate,
        "certificate": None,
        "roo_requirement": None,
        "savings_vs_mfn": Decimal("0"),
    })

    for fta in tariff_data.get("fta_rates", []):
        fta_rate = fta.get("rate_pct", mfn_rate)
        if isinstance(fta_rate, str):
            fta_rate = Decimal(fta_rate)
        agreement_code = fta.get("agreement", "FTA")
        options.append({
            "code": agreement_code,
            "rate": fta_rate,
            "certificate": CERTIFICATE_MAP.get(agreement_code, f"{agreement_code} 原产地证"),
            "roo_requirement": ROO_NOTES.get(agreement_code),
            "savings_vs_mfn": mfn_rate - fta_rate,
        })

    options.sort(key=lambda x: x["rate"])
    best = options[0] if options else None

    additional_total = sum(
        ad.get("rate_pct", Decimal("0")) for ad in tariff_data.get("additional_duties", [])
    )

    notes_parts = []
    if additional_total > 0:
        notes_parts.append(f"附加税 {additional_total}% 来自 {origin} 原产(FTA不能免除附加税)")
    if best and best["code"] != "MFN" and best["savings_vs_mfn"] > 0:
        notes_parts.append(f"使用 {best['code']} 可节省 {best['savings_vs_mfn']}% 关税")
    if best and best["roo_requirement"]:
        notes_parts.append(f"原产地规则: {best['roo_requirement']}")

    return {
        "hs_code": hs_code,
        "origin": origin,
        "dest": dest,
        "available_agreements": options,
        "best_option": best["code"] if best else None,
        "best_rate": best["rate"] if best else None,
        "best_certificate": best["certificate"] if best else None,
        "additional_duty_total": additional_total,
        "notes": " | ".join(notes_parts) if notes_parts else "MFN is the only option",
    }


def compare_origins(db: Session, hs_code: str, dest: str,
                    origins: List[str] = None) -> List[dict]:
    if not origins:
        origins = ["CN", "VN", "TH", "MY", "ID"]

    results = []
    for origin in origins:
        rec = recommend_fta(db, hs_code, origin, dest)
        results.append({
            "origin": origin,
            "best_agreement": rec.get("best_option"),
            "best_rate": rec.get("best_rate"),
            "additional_duty": rec.get("additional_duty_total"),
            "total_effective": (rec.get("best_rate") or Decimal("0")) + (rec.get("additional_duty_total") or Decimal("0")),
            "certificate": rec.get("best_certificate"),
            "notes": rec.get("notes"),
        })

    results.sort(key=lambda x: x["total_effective"])
    return results
