from __future__ import annotations
"""国家与HS编码骨架（从 app/ 迁移）"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base, TimestampMixin


class Country(Base, TimestampMixin):
    __tablename__ = "country"
    id = Column(Integer, primary_key=True)
    iso2 = Column(String(2), unique=True, nullable=False, index=True)
    iso3 = Column(String(3))
    name_cn = Column(String(100))
    name_en = Column(String(100))
    region = Column(String(50))
    customs_url = Column(String(500))
    hs_digit_length = Column(Integer)
    currency_code = Column(String(3))


class HSNomenclature(Base, TimestampMixin):
    __tablename__ = "hs_nomenclature"
    id = Column(Integer, primary_key=True)
    hs_code = Column(String(10), unique=True, nullable=False, index=True)
    description_en = Column(Text)
    description_cn = Column(Text)
    section = Column(String(10))
    chapter = Column(String(10))
    heading = Column(String(10))
    level = Column(String(10))  # SECTION / CHAPTER / HEADING / SUBHEADING
