"""导入更多国税则数据

从 hts_source.db 导入 AU, BR, CA, EU, GB, MX, TW 等国税则数据。
同时自动补全缺少的国家记录。

使用:
  cd backend
  python3 scripts/import_additional_tariff_data.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.country_hs import Country
from app.models.tariff import NationalTariffLine
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SRC_DB = DATA_DIR / "hts_source.db"


# ─── 缺失的国家记录 ───
MISSING_COUNTRIES = [
    {"iso2": "BR", "iso3": "BRA", "name_cn": "巴西", "name_en": "Brazil", "currency_code": "BRL"},
    {"iso2": "CA", "iso3": "CAN", "name_cn": "加拿大", "name_en": "Canada", "currency_code": "CAD"},
    {"iso2": "MX", "iso3": "MEX", "name_cn": "墨西哥", "name_en": "Mexico", "currency_code": "MXN"},
    {"iso2": "TW", "iso3": "TWN", "name_cn": "台湾", "name_en": "Taiwan", "currency_code": "TWD"},
]

# ─── 待导入配置: (iso2, src_table, hs_col, desc_cols) ───
IMPORT_CONFIGS = [
    ("AU", "au_tariff_items", "reference_no", ("description",)),
    ("BR", "br_tariff_items", "ncm_code", ("description_pt",)),
    ("CA", "ca_tariff_items", "tariff_item", ("description",)),
    ("DE", "eu_tariff_items", "commodity_code", ("description",)),
    ("GB", "uk_tariff_items", "commodity_code", ("description",)),
    ("MX", "mx_tariff_items", "fraccion", ("description",)),
    ("TW", "tw_tariff_items", "hs_code", ("hs_cname", "hs_ename")),
]


def ensure_missing_countries():
    """添加缺失的国家记录"""
    db = SessionLocal()
    try:
        existing = {c.iso2 for c in db.query(Country).all()}
        added = 0
        for c in MISSING_COUNTRIES:
            if c["iso2"] not in existing:
                db.add(Country(**c))
                added += 1
        if added:
            db.commit()
            logger.success(f"Added {added} new countries")
        else:
            logger.info("All countries already exist")
    finally:
        db.close()


def get_cid_from_db(db: sqlite3.Connection, iso2: str) -> int | None:
    """从 gtcs.db 获取 country id"""
    row = db.execute("SELECT id FROM country WHERE iso2=? COLLATE NOCASE", (iso2,)).fetchone()
    return row[0] if row else None


def import_country_tariff(
    dst: sqlite3.Connection,
    src: sqlite3.Connection,
    iso2: str,
    src_table: str,
    hs_col: str,
    desc_cols: tuple[str, ...],
) -> int:
    """导入特定国家税则表"""
    cid = get_cid_from_db(dst, iso2)
    if not cid:
        logger.warning(f"{iso2} not found in country table, skipping")
        return 0

    exist = dst.execute(
        "SELECT COUNT(*) FROM national_tariff_line WHERE country_id=?", (cid,)
    ).fetchone()[0]
    if exist > 100:
        logger.info(f"{iso2} already has {exist} lines, skipping")
        return 0

    # 获取源表可用列
    src_cols = {r[1] for r in src.execute(f"PRAGMA table_info({src_table})").fetchall()}
    available_desc = [c for c in desc_cols if c in src_cols]

    if hs_col not in src_cols:
        logger.warning(f"{src_table} has no '{hs_col}' column, available: {src_cols}")
        return 0

    hs_col_expr = f"CAST({hs_col} AS TEXT)"
    desc_expr = ", ".join(available_desc) if available_desc else "NULL AS placeholder"

    rows = src.execute(
        f"SELECT DISTINCT {hs_col_expr}, {desc_expr} FROM {src_table} ORDER BY 1"
    ).fetchall()

    if not rows:
        logger.warning(f"{src_table} is empty")
        return 0

    batch = []
    count = 0
    for row in rows:
        raw = str(row[0] or "")
        hs_code = raw.replace(".", "").replace(" ", "").strip()
        if len(hs_code) < 4 or not hs_code.isdigit():
            continue
        desc_parts = [str(row[i] or "") for i in range(1, len(row))]
        desc = " ".join(p for p in desc_parts if p)
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


def main():
    if not SRC_DB.exists():
        logger.error(f"Source DB not found: {SRC_DB}")
        sys.exit(1)

    # 1. 补全国家记录
    ensure_missing_countries()

    # 2. 连接数据库
    src = sqlite3.connect(str(SRC_DB))
    dst = sqlite3.connect(str(DATA_DIR / "gtcs.db"))

    total = 0
    try:
        for iso2, src_table, hs_col, desc_cols in IMPORT_CONFIGS:
            n = import_country_tariff(dst, src, iso2, src_table, hs_col, desc_cols)
            total += n

        logger.success(f"Total imported: {total} lines across {len(IMPORT_CONFIGS)} countries")

        # 打印汇总
        for row in dst.execute(
            "SELECT c.iso2, c.name_cn, COUNT(ntl.id) "
            "FROM country c LEFT JOIN national_tariff_line ntl ON c.id=ntl.country_id "
            "GROUP BY c.id HAVING COUNT(ntl.id) > 0 ORDER BY c.iso2"
        ).fetchall():
            print(f"  {row[0]:4s} {row[1]:12s} {row[2]:>6d} lines")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
