from __future__ import annotations
"""用户与角色（从 gtcs-server 迁移）"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    display_name = Column(String(100))
    email = Column(String(200))
    role = Column(String(20), default="viewer")  # admin / customs_mgr / customs_staff / compliance / viewer
    phone = Column(String(30))
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
