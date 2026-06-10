"""种子数据 — 初始化系统所需的基准数据

包含:
  1. 国家基础数据
  2. 贸易协定数据 (RCEP / ACFTA / CPTPP 等)
  3. 默认管理员用户
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.country_hs import Country
from app.models.tariff import TradeAgreement
from app.models.user import User
from loguru import logger


COUNTRIES = [
    {"iso2": "US", "iso3": "USA", "name_cn": "美国", "name_en": "United States", "currency_code": "USD"},
    {"iso2": "CN", "iso3": "CHN", "name_cn": "中国", "name_en": "China", "currency_code": "CNY"},
    {"iso2": "VN", "iso3": "VNM", "name_cn": "越南", "name_en": "Vietnam", "currency_code": "VND"},
    {"iso2": "TH", "iso3": "THA", "name_cn": "泰国", "name_en": "Thailand", "currency_code": "THB"},
    {"iso2": "MY", "iso3": "MYS", "name_cn": "马来西亚", "name_en": "Malaysia", "currency_code": "MYR"},
    {"iso2": "ID", "iso3": "IDN", "name_cn": "印度尼西亚", "name_en": "Indonesia", "currency_code": "IDR"},
    {"iso2": "JP", "iso3": "JPN", "name_cn": "日本", "name_en": "Japan", "currency_code": "JPY"},
    {"iso2": "KR", "iso3": "KOR", "name_cn": "韩国", "name_en": "South Korea", "currency_code": "KRW"},
    {"iso2": "DE", "iso3": "DEU", "name_cn": "德国", "name_en": "Germany", "currency_code": "EUR"},
    {"iso2": "GB", "iso3": "GBR", "name_cn": "英国", "name_en": "United Kingdom", "currency_code": "GBP"},
    {"iso2": "IN", "iso3": "IND", "name_cn": "印度", "name_en": "India", "currency_code": "INR"},
    {"iso2": "AU", "iso3": "AUS", "name_cn": "澳大利亚", "name_en": "Australia", "currency_code": "AUD"},
    {"iso2": "EU", "iso3": "EU", "name_cn": "欧盟", "name_en": "European Union", "currency_code": "EUR"},
    {"iso2": "SG", "iso3": "SGP", "name_cn": "新加坡", "name_en": "Singapore", "currency_code": "SGD"},
    {"iso2": "PH", "iso3": "PHL", "name_cn": "菲律宾", "name_en": "Philippines", "currency_code": "PHP"},
]

AGREEMENTS = [
    {
        "code": "RCEP",
        "name_cn": "区域全面经济伙伴关系协定",
        "name_en": "Regional Comprehensive Economic Partnership",
        "member_countries": '["CN","JP","KR","AU","NZ","VN","TH","MY","ID","PH","SG","BN","KH","LA","MM"]',
        "effective_date": date(2022, 1, 1),
    },
    {
        "code": "ACFTA",
        "name_cn": "中国-东盟自由贸易区",
        "name_en": "ASEAN-China Free Trade Area",
        "member_countries": '["CN","VN","TH","MY","ID","PH","SG","BN","KH","LA","MM"]',
        "effective_date": date(2010, 1, 1),
    },
    {
        "code": "CPTPP",
        "name_cn": "全面与进步跨太平洋伙伴关系协定",
        "name_en": "Comprehensive and Progressive Agreement for Trans-Pacific Partnership",
        "member_countries": '["JP","CA","AU","NZ","SG","VN","MY","BN","MX","PE","CL"]',
        "effective_date": date(2018, 12, 30),
    },
    {
        "code": "USMCA",
        "name_cn": "美墨加协定",
        "name_en": "United States-Mexico-Canada Agreement",
        "member_countries": '["US","MX","CA"]',
        "effective_date": date(2020, 7, 1),
    },
    {
        "code": "EVFTA",
        "name_cn": "欧盟-越南自由贸易协定",
        "name_en": "EU-Vietnam Free Trade Agreement",
        "member_countries": '["VN","EU"]',
        "effective_date": date(2020, 8, 1),
    },
    {
        "code": "EU_GSP",
        "name_cn": "欧盟普惠制",
        "name_en": "EU Generalized Scheme of Preferences",
        "member_countries": '["VN","TH","ID","PH","KH","LA","MM","BD"]',
        "effective_date": date(2014, 1, 1),
    },
    {
        "code": "AIFTA",
        "name_cn": "东盟-印度自由贸易区",
        "name_en": "ASEAN-India Free Trade Area",
        "member_countries": '["IN","VN","TH","MY","ID","PH","SG","BN","KH","LA","MM"]',
        "effective_date": date(2010, 1, 1),
    },
    {
        "code": "KAFTA",
        "name_cn": "韩国-东盟自由贸易协定",
        "name_en": "Korea-ASEAN FTA",
        "member_countries": '["KR","VN","TH","MY","ID","PH","SG","BN","KH","LA","MM"]',
        "effective_date": date(2007, 6, 1),
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. 国家数据
        for c in COUNTRIES:
            existing = db.query(Country).filter(Country.iso2 == c["iso2"]).first()
            if not existing:
                db.add(Country(**c))
                logger.info(f"  Country: {c['iso2']} - {c['name_cn']}")
        total_countries = db.query(Country).count()
        logger.info(f"Countries: {total_countries}")

        # 2. 贸易协定
        for a in AGREEMENTS:
            existing = db.query(TradeAgreement).filter(TradeAgreement.code == a["code"]).first()
            if not existing:
                db.add(TradeAgreement(**a))
                logger.info(f"  FTA: {a['code']} - {a['name_cn']}")
        total_fta = db.query(TradeAgreement).count()
        logger.info(f"Trade Agreements: {total_fta}")

        # 3. 默认管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(User(
                username="admin",
                hashed_password=hash_password("admin123"),
                display_name="System Admin",
                role="admin",
                is_active=True,
            ))
            logger.info("  Default admin: admin / admin123")
        else:
            logger.info("  Admin user already exists")

        db.commit()
        logger.success("Seed data complete!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
