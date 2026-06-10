from __future__ import annotations
"""JWT 认证 + RBAC — 从 gtcs-server 迁移并增强"""
from datetime import datetime, timedelta, timezone
from functools import wraps
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, settings.effective_secret_key, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None  # 匿名用户
    from app.models.user import User
    try:
        payload = jwt.decode(token, settings.effective_secret_key, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
    return db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()


def require_user(roles: List[str] | None = None):
    """Dependency: 要求登录 + 可选角色"""
    def _require(current_user=Depends(get_current_user)):
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
        if roles and current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user
    return _require


# 快捷权限依赖
require_admin = require_user(["admin"])
require_customs_mgr = require_user(["admin", "customs_mgr"])
require_customs_staff = require_user(["admin", "customs_mgr", "customs_staff"])
