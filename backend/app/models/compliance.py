from __future__ import annotations
from typing import Optional, List, Dict, Any
"""合规 — 出口管制 + 进口认证要求 + HS归类档案 + 预裁定

合并 app/models/ 的 export_control.py, import_requirement.py, hs_classification.py
"""
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey
from app.core.database import Base, TimestampMixin


class ExportControlList(Base, TimestampMixin):
    """出口管制清单"""
    __tablename__ = "export_control_list"
    id = Column(Integer, primary_key=True)
    list_type = Column(String(20), nullable=False)  # ENTITY_LIST / SDN / MILITARY / DUAL_USE
    issuer = Column(String(50))  # BIS / OFAC / MOFCOM
    ref_number = Column(String(100))
    name = Column(String(300), nullable=False)
    name_cn = Column(String(300))
    country = Column(String(2))
    reason = Column(Text)
    publish_date = Column(Date)
    source_url = Column(String(500))
    is_active = Column(Integer, default=1)


class ImportRequirement(Base, TimestampMixin):
    """进口认证要求"""
    __tablename__ = "import_requirement"
    id = Column(Integer, primary_key=True)
    country = Column(String(2), nullable=False)
    hs_code = Column(String(10))
    requirement_type = Column(String(50))  # CE / FCC / CCC / RoHS / REACH
    requirement_name = Column(String(200))
    description = Column(Text)
    issuing_authority = Column(String(200))
    is_mandatory = Column(Integer, default=1)
    source_url = Column(String(500))


class HSClassificationRecord(Base, TimestampMixin):
    """HS归类决策档案 — 完整字段版"""
    __tablename__ = "hs_classification_record"
    id = Column(Integer, primary_key=True)
    product_code = Column(String(30))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name_cn = Column(String(200))
    product_name_en = Column(String(200))
    product_description = Column(Text)
    brand = Column(String(100))
    model = Column(String(100))
    specifications = Column(Text)
    material_composition = Column(Text)
    function_description = Column(Text)
    use_purpose = Column(Text)

    classified_hs_code = Column(String(15), nullable=False)
    classified_country_id = Column(Integer, ForeignKey("country.id"))
    classification_basis = Column(String(50))  # PRE_RULING / SELF_CLASSIFY / CUSTOMS_RULING
    confidence_level = Column(String(10))  # HIGH / MEDIUM / LOW

    ruling_number = Column(String(100))
    ruling_country = Column(String(2))
    ruling_date = Column(Date)
    ruling_hs_code = Column(String(15))
    ruling_product_description = Column(Text)
    ruling_key_reasoning = Column(Text)
    ruling_source_url = Column(String(500))

    classification_notes = Column(Text)
    key_classification_factors = Column(Text)
    alternative_hs_codes = Column(Text)
    rejection_reasons = Column(Text)
    excluded_codes = Column(Text)

    classified_by = Column(String(50))
    reviewed_by = Column(String(50))
    approved_by = Column(String(50))
    approved_date = Column(Date)
    valid_from = Column(Date)
    valid_to = Column(Date)
    status = Column(String(20), default="ACTIVE")
    supporting_documents = Column(Text)


class HSRulingReference(Base, TimestampMixin):
    """海关预裁定案例库"""
    __tablename__ = "hs_ruling_reference"
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("country.id"))
    country = Column(String(2))
    hs_code = Column(String(15))
    product_name = Column(String(200))
    product_description = Column(Text)
    ruling_number = Column(String(100), unique=True)
    ruling_type = Column(String(30))  # CN_PRE_CLASSIFICATION / US_CBP_RULING / EU_EBTI
    issuing_authority = Column(String(200))
    ruling_date = Column(Date)
    expiry_date = Column(Date)
    decision = Column(Text)
    legal_basis = Column(Text)
    classification_reasoning = Column(Text)
    key_factors = Column(Text)
    exclusion_notes = Column(Text)
    source_url = Column(String(500))
    full_text = Column(Text)
