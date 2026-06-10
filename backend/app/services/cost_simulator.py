from __future__ import annotations
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.tariff_service import lookup_tariff


def simulate_cost(db: Session, hs_code: str, dest_country: str, scenarios: List[dict]):
    results = []

    for scenario in scenarios:
        origin = scenario["origin"]
        fob = Decimal(str(scenario["fob"]))
        freight = Decimal(str(scenario.get("freight", 0)))
        insurance = Decimal(str(scenario.get("insurance", 0)))
        cif = fob + freight + insurance

        tariff_data = lookup_tariff(db, hs_code, dest_country, origin)

        mfn_rate = Decimal("0")
        fta_rate = None
        fta_name = None
        additional_rate = Decimal("0")
        additional_type = None

        if tariff_data:
            mfn_rate = tariff_data.get("mfn_rate") or Decimal("0")

            for fta in tariff_data.get("fta_rates", []):
                r = fta.get("rate_pct")
                if r is not None and (fta_rate is None or r < fta_rate):
                    fta_rate = r
                    fta_name = fta.get("agreement")

            for ad in tariff_data.get("additional_duties", []):
                additional_rate += ad.get("rate_pct", Decimal("0"))
                additional_type = ad.get("duty_type")

        best_base_rate = fta_rate if fta_rate is not None and fta_rate < mfn_rate else mfn_rate
        total_rate = best_base_rate + additional_rate
        duty_amount = cif * total_rate / Decimal("100")
        landed_cost = cif + duty_amount

        results.append({
            "origin": origin,
            "fob": fob,
            "freight": freight,
            "insurance": insurance,
            "cif": cif,
            "mfn_rate": mfn_rate,
            "fta_rate": fta_rate,
            "fta_name": fta_name,
            "additional_duty_rate": additional_rate,
            "additional_duty_type": additional_type,
            "total_rate": total_rate,
            "duty_amount": duty_amount.quantize(Decimal("0.01")),
            "landed_cost": landed_cost.quantize(Decimal("0.01")),
        })

    results.sort(key=lambda x: x["landed_cost"])
    recommendation = results[0]["origin"] if results else None

    cn_landed = next((r["landed_cost"] for r in results if r["origin"] == "CN"), None)
    best_landed = results[0]["landed_cost"] if results else None
    saving = (cn_landed - best_landed) if cn_landed and best_landed and cn_landed > best_landed else Decimal("0")

    return {
        "hs_code": hs_code,
        "dest_country": dest_country,
        "comparisons": results,
        "recommendation": recommendation,
        "saving_vs_cn": saving.quantize(Decimal("0.01")),
    }
