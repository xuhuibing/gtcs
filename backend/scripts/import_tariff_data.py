"""税则数据导入脚本 v2

数据源: 税则库/ 目录下的 data.zip (含 130MB hts.db 多国税则)
              + VN.zip / THAI.zip (补充数据)

跳过: china_tariff_2026.pdf (用户指定不导入)

使用:
  python scripts/import_tariff_data.py              # 导入全部
  python scripts/import_tariff_data.py --country US  # 仅导入美国
"""
from __future__ import annotations
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine, Base
from app.models.country_hs import Country
from app.models.tariff import NationalTariffLine, TariffRate, TradeAgreement, AdditionalDuty
from loguru import logger

import os

TAX_DIR = Path(os.environ.get("GTCS_TAX_DIR", "/Users/bingxu/GTCS- 全球关务系统:税则/税则库"))
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "gtcs.db"
SRC_DB = DATA_DIR / "hts_source.db"

# ─── country code → internal id cache ────────────────
COUNTRY_IDS: dict[str, int] = {}


def _get_cid(db, iso2: str) -> int | None:
    if iso2 not in COUNTRY_IDS:
        row = db.execute("SELECT id FROM country WHERE iso2=? COLLATE NOCASE", (iso2,)).fetchone()
        if row:
            COUNTRY_IDS[iso2] = row[0]
    return COUNTRY_IDS.get(iso2)


# ─── US HTS ──────────────────────────────────────────
def clean_all_tariff_data(dst: sqlite3.Connection) -> None:
    """Clean all tariff data."""
    logger.warning("Cleaning all tariff data...")
    dst.execute("DELETE FROM additional_duty")
    dst.execute("DELETE FROM tariff_rate")
    dst.execute("DELETE FROM national_tariff_line")
    dst.commit()
    logger.success("All tariff data cleaned")


def import_us_hts(src: sqlite3.Connection, dst: sqlite3.Connection) -> None:
    """从 hts_subheadings + hts_rates 导入美国 HTS 税则"""
    us_id = _get_cid(dst, "US")
    if not us_id:
        logger.warning("US country not found, skipping")
        return

    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (us_id,)
    ).fetchone()[0]
    if exist > 50000:
        logger.info(f"US HTS already imported ({exist} lines), skipping"); return

    hts = src.execute(
        "SELECT hts_code, description, unit1, unit2 FROM hts_subheadings ORDER BY hts_code"
    ).fetchall()
    rates = src.execute(
        "SELECT hts_code, rate_type, rate_value, rate_text, effective_date, expiration_date "
        "FROM hts_rates ORDER BY hts_code"
    ).fetchall()
    s122 = src.execute(
        "SELECT hts_code, annex FROM s122_exempt"
    ).fetchall()

    logger.info(f"US HTS: {len(hts)} subheadings, {len(rates)} rates, {len(s122)} S122 items")

    # Build rates_lookup: hts_code -> list of (rate_type, rate_value, rate_text)
    rates_lookup: dict[str, list] = {}
    for r in rates:
        rates_lookup.setdefault(r[0], []).append(r)

    # Import lines in batches, capturing real auto-increment IDs for rate linkage
    line_batch = []           # [(country_id, local_code, desc, None), ...]
    pending_rates = []        # [(batch_idx, rate_type, rate_val, rate_text), ...]
    line_count, rate_count = 0, 0

    for row in hts:
        hts_code = row[0]
        desc = row[1] or ""
        local_code = hts_code.replace(".", "").replace(" ", "")
        batch_idx = len(line_batch)  # position within current batch
        line_batch.append((us_id, local_code, desc, None))
        line_count += 1

        # Stage rates for this subheading, keyed by batch position
        for r in rates_lookup.get(hts_code, []):
            rate_type = r[1] or "MFN"
            rate_val = None
            if r[2] is not None:
                try:
                    rate_val = float(r[2].replace("%", "").strip()) if isinstance(r[2], str) else float(r[2])
                except (ValueError, TypeError):
                    rate_val = None
            rdesc = r[3] or ""
            pending_rates.append((batch_idx, rate_type, rate_val, rdesc))
            rate_count += 1

        if len(line_batch) >= 500:
            _flush_line_and_rate_batch(dst, line_batch, pending_rates)
            line_batch, pending_rates = [], []
            dst.commit()

    if line_batch:
        _flush_line_and_rate_batch(dst, line_batch, pending_rates)
    dst.commit()
    logger.success(f"US HTS imported: {line_count} lines, {rate_count} rates")

    # Section 122 → AdditionalDuty (after all lines are imported)
    ad_exist = dst.execute(
        "SELECT COUNT(*) FROM additional_duty WHERE country_id=? AND duty_type='SEC301'", (us_id,)
    ).fetchone()[0]
    if ad_exist == 0:
        ad_batch = []
        for r in s122:
            hts_code = r[0]
            annex = r[1]
            local_code = hts_code.replace(".", "").replace(" ", "")
            tl = dst.execute(
                "SELECT id FROM national_tariff_line WHERE country_id=? AND local_code LIKE ? LIMIT 1",
                (us_id, f"{local_code}%"),
            ).fetchone()
            if tl:
                ad_batch.append((us_id, tl[0], "SEC301", "CN", 25.0, "Section 122", f"Annex {annex}"))
            if len(ad_batch) >= 200:
                dst.executemany(
                    "INSERT INTO additional_duty (country_id, tariff_line_id, duty_type, target_origin, rate_pct, legal_basis, case_number) VALUES (?,?,?,?,?,?,?)",
                    ad_batch,
                )
                ad_batch = []
        if ad_batch:
            dst.executemany(
                "INSERT INTO additional_duty (country_id, tariff_line_id, duty_type, target_origin, rate_pct, legal_basis, case_number) VALUES (?,?,?,?,?,?,?)",
                ad_batch,
            )
        dst.commit()
        logger.success(f"Section 122: {len(s122)} duties imported")


def _flush_line_and_rate_batch(dst: sqlite3.Connection, line_batch: list, pending_rates: list) -> None:
    """Insert a batch of lines, then insert rates using the real auto-increment IDs."""
    max_before = dst.execute("SELECT COALESCE(MAX(id), 0) FROM national_tariff_line").fetchone()[0]
    dst.executemany(
        "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
        line_batch,
    )
    batch_first_id = max_before + 1

    rate_inserts = []
    for batch_idx, rate_type, rate_val, rdesc in pending_rates:
        line_id = batch_first_id + batch_idx
        rate_inserts.append((line_id, rate_type, None, rate_val, rdesc))
    if rate_inserts:
        dst.executemany(
            "INSERT INTO tariff_rate (tariff_line_id, rate_type, agreement_id, ad_valorem_rate, source_url) VALUES (?,?,?,?,?)",
            rate_inserts,
        )


# ─── Generic country tariff importer ────────────────
def import_country_tariff(
    dst: sqlite3.Connection,
    src: sqlite3.Connection,
    iso2: str,
    src_table: str,
    hs_col: str = "hs_code",
    desc_cols: tuple[str, ...] = ("title_en",),
) -> int:
    """导入特定国家税则表到 national_tariff_line"""
    cid = _get_cid(dst, iso2)
    if not cid:
        logger.warning(f"{iso2} not found in country table, skipping"); return 0

    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (cid,)
    ).fetchone()[0]
    if exist > 100:
        logger.info(f"{iso2} already has {exist} lines, skipping"); return 0

    # Get available columns
    src_cols = {r[1] for r in src.execute(f"PRAGMA table_info({src_table})").fetchall()}
    available_desc = [c for c in desc_cols if c in src_cols]
    if not available_desc:
        available_desc = ["description"] if "description" in src_cols else []

    rows = src.execute(f"SELECT {hs_col}, {','.join(available_desc)} FROM {src_table} ORDER BY {hs_col}").fetchall()
    if not rows:
        logger.warning(f"{src_table} is empty"); return 0

    batch = []
    count = 0
    for row in rows:
        hs_code = str(row[0] or "").replace(".", "").replace(" ", "")
        if len(hs_code) < 4:
            continue
        desc = " ".join(str(row[i] or "") for i in range(1, len(row)))
        batch.append((cid, hs_code, desc, None))
        count += 1
        if len(batch) >= 500:
            dst.executemany(
                "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
                batch,
            )
            batch = []
    if batch:
        dst.executemany(
            "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
            batch,
        )
    dst.commit()
    logger.success(f"{iso2} ({src_table}): {count} lines imported")
    return count


# ─── VN from hts_source.db (has 30+ rate columns) ───
def import_vn_from_source(src: sqlite3.Connection, dst: sqlite3.Connection) -> None:
    """越南税则 (含 FTA 税率)"""
    vn_id = _get_cid(dst, "VN")
    if not vn_id:
        return
    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (vn_id,)
    ).fetchone()[0]
    if exist > 100:
        logger.info(f"VN already imported ({exist} lines)"); return

    cols = [r[1] for r in src.execute("PRAGMA table_info(vn_tariff_items)").fetchall()]
    desc_cols = [c for c in ["title_en", "title_vi"] if c in cols]
    rate_cols = [c for c in cols if c.startswith("rate_") and c != "rate_env"]
    hs_col = "hs_code" if "hs_code" in cols else "hs_code_formatted"

    rows = src.execute(
        f"SELECT {hs_col}, {','.join(desc_cols)}, {','.join(rate_cols)} FROM vn_tariff_items ORDER BY {hs_col}"
    ).fetchall()

    cnt = 0
    for row in rows:
        hs_code = str(row[0] or "").replace(".", "").replace(" ", "")
        if len(hs_code) < 4:
            continue
        desc = " ".join(str(row[i] or "") for i in range(1, len(desc_cols) + 1))
        rates_data = {rate_cols[i]: row[1 + len(desc_cols) + i] for i in range(len(rate_cols))}
        dst.execute(
            "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
            (vn_id, hs_code, desc, json.dumps(rates_data, ensure_ascii=False) if rates_data else None),
        )
        cnt += 1
        if cnt % 1000 == 0:
            dst.commit()
    dst.commit()
    logger.success(f"VN tariff: {cnt} lines with FTA rates imported")


# ─── TH from THAI.zip JSONL ─────────────────────────
def import_thai_tariff(dst: sqlite3.Connection) -> None:
    th_id = _get_cid(dst, "TH")
    if not th_id:
        return
    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (th_id,)
    ).fetchone()[0]
    if exist > 100:
        logger.info(f"TH already imported ({exist} lines)"); return

    thai_zip = TAX_DIR / "THAI.zip"
    if not thai_zip.exists():
        logger.warning("THAI.zip not found"); return

    with zipfile.ZipFile(thai_zip) as zf:
        jsonl_files = [n for n in zf.namelist() if n.endswith(".jsonl")]
        if not jsonl_files:
            logger.warning("No JSONL in THAI.zip"); return
        content = zf.read(jsonl_files[0]).decode("utf-8")

    cnt = 0
    batch = []
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        hs = rec.get("hs_code", "").replace(".", "").replace(" ", "")
        if len(hs) < 4:
            continue
        desc = rec.get("description_en") or rec.get("product_name", "")
        batch.append((th_id, hs, desc, None))
        cnt += 1
        if len(batch) >= 500:
            dst.executemany(
                "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
                batch,
            )
            batch = []
    if batch:
        dst.executemany(
            "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
            batch,
        )
    dst.commit()
    logger.success(f"TH tariff: {cnt} lines imported")


# ─── MY from hts_source.db ──────────────────────────
def import_my_tariff(src: sqlite3.Connection, dst: sqlite3.Connection) -> None:
    my_id = _get_cid(dst, "MY")
    if not my_id:
        return
    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (my_id,)
    ).fetchone()[0]
    if exist > 100:
        logger.info(f"MY already imported ({exist} lines)"); return

    cols = [r[1] for r in src.execute("PRAGMA table_info(my_tariff_items)").fetchall()]
    rate_cols = [c for c in cols if c.startswith("rate_")]
    my_rows = src.execute(
        f"SELECT hs_code, description, {','.join(rate_cols)} FROM my_tariff_items ORDER BY hs_code"
    ).fetchall()

    batch = []
    cnt = 0
    for r in my_rows:
        hs = str(r[0] or "").replace(".", "").replace(" ", "")
        if len(hs) < 4:
            continue
        desc = str(r[1] or "")
        batch.append((my_id, hs, desc, None))
        cnt += 1
        if len(batch) >= 500:
            dst.executemany(
                "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
                batch,
            )
            batch = []
    if batch:
        dst.executemany(
            "INSERT INTO national_tariff_line (country_id, local_code, description_en, description_cn) VALUES (?,?,?,?)",
            batch,
        )
    dst.commit()
    logger.success(f"MY tariff: {cnt} lines imported")


def ensure_countries_in_db():
    """Create country records from src DB or defaults"""
    db = SessionLocal()
    try:
        existing = db.query(Country).count()
        if existing > 0:
            logger.info(f"Countries already exist: {existing}")
            return

        from app.core.security import hash_password
        from app.models.user import User
        from app.models.tariff import TradeAgreement

        countries = [
            {"iso2": "US", "iso3": "USA", "name_cn": "美国", "name_en": "United States", "currency_code": "USD"},
            {"iso2": "CN", "iso3": "CHN", "name_cn": "中国", "name_en": "China", "currency_code": "CNY"},
            {"iso2": "VN", "iso3": "VNM", "name_cn": "越南", "name_en": "Vietnam", "currency_code": "VND"},
            {"iso2": "TH", "iso3": "THA", "name_cn": "泰国", "name_en": "Thailand", "currency_code": "THB"},
            {"iso2": "MY", "iso3": "MYS", "name_cn": "马来西亚", "name_en": "Malaysia", "currency_code": "MYR"},
            {"iso2": "ID", "iso3": "IDN", "name_cn": "印度尼西亚", "name_en": "Indonesia", "currency_code": "IDR"},
            {"iso2": "JP", "iso3": "JPN", "name_cn": "日本", "name_en": "Japan", "currency_code": "JPY"},
            {"iso2": "KR", "iso3": "KOR", "name_cn": "韩国", "name_en": "South Korea", "currency_code": "KRW"},
            {"iso2": "IN", "iso3": "IND", "name_cn": "印度", "name_en": "India", "currency_code": "INR"},
            {"iso2": "AU", "iso3": "AUS", "name_cn": "澳大利亚", "name_en": "Australia", "currency_code": "AUD"},
            {"iso2": "DE", "iso3": "DEU", "name_cn": "德国", "name_en": "Germany", "currency_code": "EUR"},
            {"iso2": "GB", "iso3": "GBR", "name_cn": "英国", "name_en": "United Kingdom", "currency_code": "GBP"},
        ]
        for c in countries:
            db.add(Country(**c))
        db.commit()
        logger.success(f"Created {len(countries)} countries")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", help="Single country code (US/VN/TH/MY)")
    parser.add_argument("--skip-us", action="store_true", help="Skip US HTS import")
    parser.add_argument("--clean", action="store_true", help="Clean all tariff data before import")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    ensure_countries_in_db()

    if not SRC_DB.exists():
        logger.warning(f"Source DB not found: {SRC_DB}")
        logger.info("Extracting from data.zip...")
        with zipfile.ZipFile(TAX_DIR / "data.zip") as zf:
            zf.extract("hts.db", DATA_DIR)
        (DATA_DIR / "hts.db").rename(SRC_DB)

    src = sqlite3.connect(str(SRC_DB))
    dst = sqlite3.connect(str(DB_PATH))

    try:
        if args.clean:
            clean_all_tariff_data(dst)

        if args.country:
            c = args.country.upper()
            if c == "US" and not args.skip_us:
                import_us_hts(src, dst)
            elif c == "VN":
                import_vn_from_source(src, dst)
            elif c == "TH":
                import_thai_tariff(dst)
            elif c == "MY":
                import_my_tariff(src, dst)
            else:
                logger.warning(f"Unknown country: {c}")
        else:
            import_us_hts(src, dst)
            import_vn_from_source(src, dst)
            import_thai_tariff(dst)
            import_my_tariff(src, dst)

        logger.success("All tariff data imported!")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
