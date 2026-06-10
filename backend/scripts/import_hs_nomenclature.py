"""HS 命名法导入脚本 — 章节/品目/子目 中英文描述

从 hts_source.db 提取章节(2位)、品目(4位)、子目(6位) 数据，
写入主数据库 hs_nomenclature 表，并更新 national_tariff_line 的中文描述。

使用:
  cd backend
  PYTHONPATH=. python3 scripts/import_hs_nomenclature.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from loguru import logger
from app.core.database import SessionLocal
from app.models.country_hs import HSNomenclature
from app.models.tariff import NationalTariffLine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SRC_DB = DATA_DIR / "hts_source.db"


def import_chapters(db_src, dst):
    """导入 HS 章节 (2位)"""
    rows = db_src.execute("""
        SELECT chapter_code, title, COALESCE(title_cn, '') as cn
        FROM hts_chapters
        ORDER BY chapter_code
    """).fetchall()

    count = 0
    for code, title_en, title_cn in rows:
        code = code.zfill(2)
        existing = dst.query(HSNomenclature).filter(
            HSNomenclature.hs_code == code,
            HSNomenclature.level == "CHAPTER",
        ).first()
        if existing:
            existing.description_en = title_en
            existing.description_cn = title_cn or existing.description_cn
        else:
            dst.add(HSNomenclature(
                hs_code=code,
                chapter=code,
                level="CHAPTER",
                description_en=title_en,
                description_cn=title_cn or None,
            ))
        count += 1

    dst.commit()
    logger.info(f"Imported/updated {count} HS chapters")


def import_headings(db_src, dst):
    """导入 HS 品目 (4位)"""
    rows = db_src.execute("""
        SELECT heading_code, title, COALESCE(title_cn, '') as cn
        FROM hts_headings
        ORDER BY heading_code
    """).fetchall()

    count = 0
    for hcode, title_en, title_cn in rows:
        hcode = hcode.zfill(4)
        chapter = hcode[:2]
        existing = dst.query(HSNomenclature).filter(
            HSNomenclature.hs_code == hcode,
            HSNomenclature.level == "HEADING",
        ).first()
        if existing:
            existing.description_en = title_en
            existing.description_cn = title_cn or existing.description_cn
        else:
            dst.add(HSNomenclature(
                hs_code=hcode,
                chapter=chapter,
                heading=hcode,
                level="HEADING",
                description_en=title_en,
                description_cn=title_cn or None,
            ))
        count += 1

    dst.commit()
    logger.info(f"Imported/updated {count} HS headings")


def import_subheadings(db_src, dst):
    """导入 HS 子目 (6位) 中文名称"""
    rows = db_src.execute("""
        SELECT DISTINCT SUBSTR(hts_code, 1, 6) as hs6,
               chapter_code, heading_code,
               SUBSTR(hts_code, 1, 6) as sub_code,
               title_cn
        FROM hts_subheadings
        WHERE title_cn IS NOT NULL AND title_cn != ''
        AND subheading_code IS NOT NULL AND subheading_code != ''
        AND LENGTH(hts_code) >= 6
    """).fetchall()

    ns_count = 0
    for hs6, ch_code, hd_code, sub_code, title_cn in rows:
        if not hs6 or len(hs6) < 6:
            continue

        existing = dst.query(HSNomenclature).filter(
            HSNomenclature.hs_code == hs6,
            HSNomenclature.level == "SUBHEADING",
        ).first()
        if not existing:
            dst.add(HSNomenclature(
                hs_code=hs6,
                chapter=ch_code,
                heading=hd_code,
                level="SUBHEADING",
                description_cn=title_cn,
            ))
            ns_count += 1

    dst.commit()
    logger.info(f"Imported {ns_count} new HS subheadings (6-digit) with Chinese names")


def update_national_cn_descriptions(dst):
    """从 hs_nomenclature 同步中文描述到 national_tariff_line"""
    # 6位子目匹配
    sub_rows = dst.query(HSNomenclature).filter(
        HSNomenclature.level == "SUBHEADING",
        HSNomenclature.description_cn.isnot(None),
    ).all()

    updated = 0
    for s in sub_rows:
        count = (
            dst.query(NationalTariffLine)
            .filter(NationalTariffLine.local_code.like(f"{s.hs_code}%"))
            .filter(
                (NationalTariffLine.description_cn.is_(None))
                | (NationalTariffLine.description_cn == "")
            )
            .update({"description_cn": s.description_cn}, synchronize_session=False)
        )
        updated += count

    # 4位品目匹配（补充6位没覆盖到的）
    hd_rows = dst.query(HSNomenclature).filter(
        HSNomenclature.level == "HEADING",
        HSNomenclature.description_cn.isnot(None),
    ).all()
    for h in hd_rows:
        count = (
            dst.query(NationalTariffLine)
            .filter(NationalTariffLine.local_code.like(f"{h.hs_code}%"))
            .filter(
                (NationalTariffLine.description_cn.is_(None))
                | (NationalTariffLine.description_cn == "")
            )
            .update({"description_cn": h.description_cn}, synchronize_session=False)
        )
        updated += count

    dst.commit()
    logger.info(f"Updated {updated} national_tariff_line records with Chinese descriptions")


def main():
    logger.info("Starting HS nomenclature import...")

    if not SRC_DB.exists():
        logger.error(f"Source database not found: {SRC_DB}")
        return

    db_src = sqlite3.connect(str(SRC_DB))
    db_dst = SessionLocal()

    try:
        import_chapters(db_src, db_dst)
        import_headings(db_src, db_dst)
        import_subheadings(db_src, db_dst)
        update_national_cn_descriptions(db_dst)
        logger.info("HS nomenclature import completed successfully!")
    finally:
        db_src.close()
        db_dst.close()


if __name__ == "__main__":
    main()
