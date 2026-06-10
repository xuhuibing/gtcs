from __future__ import annotations
"""报关单（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from app.core.database import Base, TimestampMixin
from sqlalchemy.orm import relationship


class Declaration(Base, TimestampMixin):
    __tablename__ = "declarations"
    id = Column(Integer, primary_key=True)
    declaration_no = Column(String(30), unique=True, index=True)
    customs_no = Column(String(30))
    direction = Column(String(10))  # IMPORT / EXPORT
    status = Column(String(20), default="draft")
    # draft → submitted → query_received → amended → cleared → closed
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    factory_id = Column(Integer, ForeignKey("factories.id"))
    port_code = Column(String(10))
    trade_mode = Column(String(10))
    transport_mode = Column(String(10))
    currency = Column(String(3))
    total_value = Column(Float)
    total_qty = Column(Integer)
    consignee = Column(String(200))
    consignor = Column(String(200))
    remark = Column(Text)
    related_docs = Column(JSON)
    items = relationship("DeclarationItem", back_populates="declaration")


class DeclarationItem(Base, TimestampMixin):
    __tablename__ = "declaration_items"
    id = Column(Integer, primary_key=True)
    declaration_id = Column(Integer, ForeignKey("declarations.id"), index=True)
    item_no = Column(Integer)
    product_id = Column(Integer, ForeignKey("products.id"))
    hs_code = Column(String(15), nullable=False)
    name_cn = Column(String(200), nullable=False)
    name_en = Column(String(200))
    qty = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    total_price = Column(Float)
    currency = Column(String(3), default="USD")
    origin_country = Column(String(2))
    dest_country = Column(String(2))
    duty_rate = Column(Float)
    duty_amount = Column(Float)
    declaration = relationship("Declaration", back_populates="items")
