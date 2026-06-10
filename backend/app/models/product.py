from __future__ import annotations
"""商品主数据（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from app.core.database import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    product_code = Column(String(30), nullable=False, index=True)
    name_cn = Column(String(200), nullable=False)
    name_en = Column(String(200))
    brand = Column(String(100))
    model = Column(String(100))
    specifications = Column(Text)
    unit = Column(String(20), default="PCS")
    unit_price = Column(Float)
    currency = Column(String(3), default="USD")


class HSMapping(Base, TimestampMixin):
    __tablename__ = "hs_mappings"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    country = Column(String(2), nullable=False)
    hs_code = Column(String(15), nullable=False)
    description_local = Column(Text)
    declaration_elements = Column(Text)  # JSON: 申报要素
    is_primary = Column(Integer, default=0)


class DeclarationElement(Base, TimestampMixin):
    __tablename__ = "declaration_elements"
    id = Column(Integer, primary_key=True)
    hs_code = Column(String(15), nullable=False, index=True)
    country = Column(String(2))
    element_name = Column(String(100), nullable=False)
    element_value = Column(Text)
    sort_order = Column(Integer)
