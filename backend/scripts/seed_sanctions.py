"""受限制方制裁名单种子数据导入

从 sanctions_data.json 导入制裁名单到 screening_list 表。

使用:
  cd backend
  PYTHONPATH=. python3 scripts/seed_sanctions.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from loguru import logger
from app.core.database import SessionLocal
from app.models.screening import ScreeningList

DATA_FILE = Path(__file__).resolve().parent / "sanctions_data.json"


def load_sanctions_from_json(file_path: Path) -> list:
    """从 JSON 文件加载制裁名单"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 如果没有 JSON 文件，使用内嵌种子数据
BUILTIN_SANCTIONS = [
    {"name": "ISLAMIC REPUBLIC OF IRAN SHIPPING LINES", "name_cn": "伊朗伊斯兰共和国航运公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "KOREA UNITED DEVELOPMENT BANK", "name_cn": "朝鲜统一发展银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "KP", "program": "NORTH KOREA"},
    {"name": "KOMID", "name_cn": "朝鲜矿业开发贸易公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "KP", "program": "NORTH KOREA"},
    {"name": "HIZBULLAH", "name_cn": "真主党", "list_type": "OFAC", "id_type": "ENTITY", "country": "LB", "program": "TERRORIST"},
    {"name": "HAMAS", "name_cn": "哈马斯", "list_type": "OFAC", "id_type": "ENTITY", "country": "PS", "program": "TERRORIST"},
    {"name": "TALIBAN", "name_cn": "塔利班", "list_type": "UN", "id_type": "ENTITY", "country": "AF", "program": "TERRORIST"},
    {"name": "AL QAIDA", "name_cn": "基地组织", "list_type": "UN", "id_type": "ENTITY", "country": "ZZ", "program": "TERRORIST"},
    {"name": "ISLAMIC STATE OF IRAQ AND THE LEVANT", "name_cn": "伊拉克和黎凡特伊斯兰国", "list_type": "UN", "id_type": "ENTITY", "country": "IQ", "program": "TERRORIST"},
    {"name": "BANK SEPAH", "name_cn": "伊朗塞帕银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "BANK MELLAT", "name_cn": "伊朗梅拉特银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "BANK SADERAT IRAN", "name_cn": "伊朗萨德拉特银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "BANK TEJARAT", "name_cn": "伊朗商业银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "IRAN AIR", "name_cn": "伊朗航空", "list_type": "OFAC", "id_type": "ENTITY", "country": "IR", "program": "IRAN"},
    {"name": "SYRIAN ARAB AIRLINES", "name_cn": "叙利亚阿拉伯航空", "list_type": "OFAC", "id_type": "ENTITY", "country": "SY", "program": "SYRIA"},
    {"name": "BASHAR AL ASSAD", "name_cn": "巴沙尔·阿萨德", "list_type": "OFAC", "id_type": "INDIVIDUAL", "country": "SY", "program": "SYRIA"},
    {"name": "ALI KHAMENEI", "name_cn": "阿里·哈梅内伊", "list_type": "OFAC", "id_type": "INDIVIDUAL", "country": "IR", "program": "IRAN"},
    {"name": "KIM JONG UN", "name_cn": "金正恩", "list_type": "OFAC", "id_type": "INDIVIDUAL", "country": "KP", "program": "NORTH KOREA"},
    {"name": "UNITED AIRCRAFT CORPORATION", "name_cn": "俄罗斯联合航空制造集团", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "ROSTEC STATE CORPORATION", "name_cn": "俄罗斯国家技术集团", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "ALROSA", "name_cn": "阿尔罗萨钻石公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "GAZPROM", "name_cn": "俄罗斯天然气工业股份公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "VTB BANK", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "SBERBANK", "name_cn": "俄罗斯联邦储蓄银行", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "SEVERSTAL", "name_cn": "谢韦尔钢铁公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "URALKALI", "name_cn": "乌拉尔钾肥公司", "list_type": "OFAC", "id_type": "ENTITY", "country": "RU", "program": "UKRAINE"},
    {"name": "HUAWEI TECHNOLOGIES CO LTD", "name_cn": "华为技术有限公司", "list_type": "BIS", "id_type": "ENTITY", "country": "CN", "program": "ENTITY LIST"},
    {"name": "ZTE CORPORATION", "name_cn": "中兴通讯股份有限公司", "list_type": "BIS", "id_type": "ENTITY", "country": "CN", "program": "ENTITY LIST"},
    {"name": "AVIC CHINA", "name_cn": "中国航空工业集团", "list_type": "BIS", "id_type": "ENTITY", "country": "CN", "program": "ENTITY LIST"},
    {"name": "CETC CHINA", "name_cn": "中国电子科技集团", "list_type": "BIS", "id_type": "ENTITY", "country": "CN", "program": "ENTITY LIST"},
    {"name": "CNNPEC CHINA NUCLEAR POWER ENGINEERING CO LTD", "name_cn": "中国核电工程有限公司", "list_type": "BIS", "id_type": "ENTITY", "country": "CN", "program": "ENTITY LIST"},
]


def seed(db, data: list):
    count = 0
    for item in data:
        name = item.get("name", "").strip()
        if not name:
            continue
        existing = db.query(ScreeningList).filter(
            ScreeningList.name == name,
            ScreeningList.list_type == item.get("list_type", "OFAC"),
            ScreeningList.status == "ACTIVE",
        ).first()
        if existing:
            continue
        rec = ScreeningList(
            list_type=item.get("list_type", "OFAC"),
            id_type=item.get("id_type", "ENTITY"),
            name=name,
            name_cn=item.get("name_cn"),
            country=item.get("country"),
            program=item.get("program"),
            reason=item.get("reason"),
            status="ACTIVE",
        )
        db.add(rec)
        count += 1
    db.commit()
    return count


def main():
    logger.info("Seeding sanction list data...")
    db = SessionLocal()

    # Drop and recreate tables
    from app.models.screening import ScreeningList
    from app.core.database import engine, Base
    import sqlalchemy as sa
    insp = sa.inspect(engine)
    if insp.has_table("screening_list"):
        logger.info("screening_list table already exists")
    Base.metadata.create_all(bind=engine)

    try:
        # First try loading from JSON file
        if DATA_FILE.exists():
            data = load_sanctions_from_json(DATA_FILE)
            logger.info(f"Loaded {len(data)} entries from {DATA_FILE}")
        else:
            data = BUILTIN_SANCTIONS
            logger.info(f"Using built-in {len(data)} entries (no {DATA_FILE} found)")

        count = seed(db, data)
        logger.info(f"Imported {count} new sanction list entries")

        total = db.query(ScreeningList).count()
        logger.info(f"Total screening list entries: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
