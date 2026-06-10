from __future__ import annotations
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models.country_hs import Country, HSNomenclature
from app.models.tariff import NationalTariffLine, TariffRate, AdditionalDuty, TradeAgreement


def get_country_id(db: Session, iso2: str) -> Optional[int]:
    country = db.query(Country).filter(Country.iso2 == iso2.upper()).first()
    return country.id if country else None


def get_tariff_countries(db: Session) -> List[dict]:
    """获取有税则数据的国家列表及行数统计"""
    results = (
        db.query(
            Country.iso2,
            Country.name_en,
            Country.name_cn,
            func.count(NationalTariffLine.id).label("line_count"),
        )
        .join(NationalTariffLine, NationalTariffLine.country_id == Country.id)
        .group_by(Country.id)
        .order_by(Country.iso2)
        .all()
    )
    return [
        {
            "iso2": r.iso2,
            "name_en": r.name_en,
            "name_cn": r.name_cn,
            "line_count": r.line_count,
        }
        for r in results
    ]


def browse_tariff_lines(
    db: Session,
    country: str = "US",
    prefix: Optional[str] = None,
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Dict[str, Any]:
    """按国家浏览税则数据，支持 HS 前缀筛选和关键字搜索"""
    country_id = get_country_id(db, country)
    if not country_id:
        return {"country": country, "total": 0, "page": page, "page_size": page_size, "items": []}

    q = db.query(NationalTariffLine).filter(NationalTariffLine.country_id == country_id)

    if prefix:
        clean_prefix = prefix.replace(".", "").replace(" ", "")
        q = q.filter(NationalTariffLine.local_code.like(f"{clean_prefix}%"))
    if query:
        q = q.filter(
            NationalTariffLine.description_en.ilike(f"%{query}%")
            | NationalTariffLine.description_cn.ilike(f"%{query}%")
        )

    total = q.count()
    lines = q.order_by(NationalTariffLine.local_code).offset((page - 1) * page_size).limit(page_size).all()

    # 获取每个税目的 MFN 税率
    line_ids = [l.id for l in lines]
    mfn_rates = {}
    if line_ids:
        rates = (
            db.query(TariffRate)
            .filter(
                TariffRate.tariff_line_id.in_(line_ids),
                TariffRate.rate_type.in_({"MFN", "General", "General Rate of Duty", "1"}),
            )
            .all()
        )
        for r in rates:
            mfn_rates[r.tariff_line_id] = float(r.ad_valorem_rate) if r.ad_valorem_rate is not None else None

    items = []
    for line in lines:
        items.append({
            "id": line.id,
            "local_code": line.local_code,
            "description_en": line.description_en,
            "description_cn": line.description_cn,
            "unit": line.unit,
            "effective_year": line.effective_year,
            "mfn_rate": mfn_rates.get(line.id),
        })

    return {
        "country": country,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": items,
    }


def get_hs_chapters(db: Session, country: str = "US") -> List[dict]:
    """获取指定国家税则的 HS 章节统计 (前2位)"""
    country_id = get_country_id(db, country)
    if not country_id:
        return []

    results = (
        db.query(
            func.substr(NationalTariffLine.local_code, 1, 2).label("chapter"),
            func.count(NationalTariffLine.id).label("count"),
        )
        .filter(NationalTariffLine.country_id == country_id)
        .group_by(func.substr(NationalTariffLine.local_code, 1, 2))
        .order_by("chapter")
        .all()
    )
    return [{"chapter": r.chapter, "count": r.count} for r in results]


def get_hs_chapters_with_descriptions(db: Session, country: str = "US") -> List[dict]:
    """获取指定国家税则的 HS 章节统计及中英文描述"""
    country_id = get_country_id(db, country)
    if not country_id:
        return []

    results = (
        db.query(
            func.substr(NationalTariffLine.local_code, 1, 2).label("chapter"),
            func.count(NationalTariffLine.id).label("count"),
        )
        .filter(NationalTariffLine.country_id == country_id)
        .group_by(func.substr(NationalTariffLine.local_code, 1, 2))
        .order_by("chapter")
        .all()
    )
    # 获取章节描述
    chapter_list = []
    for r in results:
        ch_code = r.chapter
        hs_entry = db.query(HSNomenclature).filter(
            HSNomenclature.hs_code == ch_code,
            HSNomenclature.level == "CHAPTER",
        ).first()
        chapter_list.append({
            "chapter": ch_code,
            "count": r.count,
            "title_en": hs_entry.description_en if hs_entry else None,
            "title_cn": hs_entry.description_cn if hs_entry else None,
        })
    return chapter_list


def lookup_tariff(db: Session, hs_code: str, dest_country: str, origin_country: str = "CN"):
    country_id = get_country_id(db, dest_country)
    if not country_id:
        return None

    clean_code = hs_code.replace(".", "").replace(" ", "")

    tariff_line = db.query(NationalTariffLine).filter(
        NationalTariffLine.country_id == country_id,
        NationalTariffLine.local_code.like(f"{clean_code}%"),
    ).first()

    if not tariff_line:
        return None

    rates = db.query(TariffRate).filter(
        TariffRate.tariff_line_id == tariff_line.id
    ).all()

    all_duties = db.query(AdditionalDuty).filter(
        AdditionalDuty.country_id == country_id,
        AdditionalDuty.tariff_line_id == tariff_line.id,
        AdditionalDuty.target_origin == origin_country.upper(),
    ).all()

    seen_types = {}
    additional_duties = []
    for d in all_duties:
        key = d.duty_type
        if key in seen_types:
            if (d.rate_pct or 0) > (seen_types[key].rate_pct or 0):
                seen_types[key] = d
        else:
            seen_types[key] = d
    additional_duties = list(seen_types.values())

    # US HTS rate types: "General" = MFN, "Special" = FTA/preferential, "Column 2" = non-MFN
    MFN_TYPES = {"MFN", "General", "General Rate of Duty", "1"}
    SPECIAL_TYPES = {"Special", "Special Rate of Duty", "FTA"}
    COLUMN2_TYPES = {"Column 2", "Column 2 Rate of Duty", "2"}

    mfn_rate = None
    column2_rate = None
    fta_rates = []

    for r in rates:
        rt = r.rate_type.strip() if r.rate_type else ""
        if rt in MFN_TYPES:
            mfn_rate = r.ad_valorem_rate
        elif rt in COLUMN2_TYPES:
            column2_rate = r.ad_valorem_rate
        elif rt in SPECIAL_TYPES:
            agreement = db.query(TradeAgreement).filter(
                TradeAgreement.id == r.agreement_id
            ).first()
            fta_rates.append({
                "rate_type": "FTA",
                "rate_pct": r.ad_valorem_rate,
                "agreement": agreement.code if agreement else None,
                "origin_scope": r.origin_scope,
            })

    add_duty_list = []
    total_additional = Decimal("0")
    for ad in additional_duties:
        add_duty_list.append({
            "duty_type": ad.duty_type,
            "rate_pct": ad.rate_pct or Decimal("0"),
            "legal_basis": ad.legal_basis,
            "target_origin": ad.target_origin,
        })
        total_additional += ad.rate_pct or Decimal("0")

    total_rate = (mfn_rate or Decimal("0")) + total_additional

    return {
        "hs_code": hs_code,
        "country": dest_country,
        "origin_country": origin_country,
        "local_code": tariff_line.local_code,
        "description": tariff_line.description_en,
        "description_cn": tariff_line.description_cn,
        "unit": tariff_line.unit,
        "mfn_rate": mfn_rate,
        "column2_rate": column2_rate,
        "fta_rates": fta_rates,
        "additional_duties": add_duty_list,
        "total_additional_rate": total_additional,
        "total_effective_rate": total_rate,
    }


def search_hs(db: Session, query: str, country: str = "US", limit: int = 20):
    country_id = get_country_id(db, country)
    if not country_id:
        return []

    results = db.query(NationalTariffLine).filter(
        NationalTariffLine.country_id == country_id,
        NationalTariffLine.local_code.like(f"{query}%") |
        NationalTariffLine.description_en.ilike(f"%{query}%"),
    ).limit(limit).all()

    return [
        {
            "local_code": r.local_code,
            "description_en": r.description_en,
            "description_cn": r.description_cn,
            "country": country,
        }
        for r in results
    ]
