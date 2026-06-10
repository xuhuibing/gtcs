from __future__ import annotations
"""GTCS API v1 — 统一路由聚合 + 全局鉴权"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt, JWTError
from app.core.config import settings
from app.api.v1.declaration import router as declaration_router
from app.api.v1.tariff import router as tariff_router
from app.api.v1.cost import router as cost_router
from app.api.v1.fta import router as fta_router
from app.api.v1.additional_duty import router as additional_duty_router
from app.api.v1.price_risk import router as price_risk_router
from app.api.v1.hs_classification import router as hs_classification_router
from app.api.v1.auth import router as auth_router
from app.api.v1.origin import router as origin_router
from app.api.v1.enterprise import router as enterprise_router
from app.api.v1.product import router as product_router
from app.api.v1.screening import router as screening_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router

# 无需鉴权的公开路径前缀
PUBLIC_PREFIXES = ("/api/v1/auth/",)


async def verify_api_auth(request: Request):
    """全局鉴权 — 只放行 /auth/* 路径"""
    path = request.url.path
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
        return
    if any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.effective_secret_key, algorithms=[settings.ALGORITHM])
        request.state.user_id = int(payload.get("sub"))
        request.state.user_role = payload.get("role")
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")


api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_auth)])
api_router.include_router(auth_router)
api_router.include_router(tariff_router)
api_router.include_router(cost_router)
api_router.include_router(fta_router)
api_router.include_router(additional_duty_router)
api_router.include_router(price_risk_router)
api_router.include_router(hs_classification_router)
api_router.include_router(origin_router)
api_router.include_router(enterprise_router)
api_router.include_router(product_router)
api_router.include_router(screening_router)
api_router.include_router(audit_router)
api_router.include_router(dashboard_router)
api_router.include_router(declaration_router)
