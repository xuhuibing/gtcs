from __future__ import annotations
"""GTCS 全球贸易通关系统 — 统一入口"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.services.fts_service import ensure_fts_indexes
from app.models.compliance import HSRulingReference


def seed_audit_logs():
    """首次启动时填充示例审计日志"""
    from app.core.database import SessionLocal
    from app.models.audit import AuditLog
    db = SessionLocal()
    try:
        existing = db.query(AuditLog).count()
        if existing > 0:
            return
        entries = [
            AuditLog(user_id=1, username="admin", action="LOGIN", resource_type="AUTH", detail="系统管理员登录"),
            AuditLog(user_id=1, username="admin", action="QUERY", resource_type="TARIFF", detail="查询美国 HTS 税则"),
            AuditLog(user_id=1, username="admin", action="QUERY", resource_type="SCREENING", detail="筛查 'Iran Shipping'"),
            AuditLog(user_id=1, username="admin", action="CREATE", resource_type="ENTERPRISE", detail="创建企业 '华为技术有限公司'"),
            AuditLog(user_id=1, username="admin", action="CREATE", resource_type="DECLARATION", detail="创建报关单"),
            AuditLog(user_id=1, username="admin", action="UPDATE", resource_type="PRODUCT", detail="更新产品信息"),
            AuditLog(user_id=1, username="admin", action="EXPORT", resource_type="REPORT", detail="导出关税分析报告"),
        ]
        for e in entries:
            db.add(e)
        db.commit()
        logger.success("Seeded demo audit logs")
    finally:
        db.close()


def seed_hs_rulings():
    """填充海关预裁定案例库"""
    from app.core.database import SessionLocal
    from datetime import date
    db = SessionLocal()
    try:
        existing = db.query(HSRulingReference).count()
        if existing > 0:
            return
        rulings = [
            # 中国海关预裁定
            {"country": "CN", "hs_code": "85285200", "product_name": "交互式智能平板(触控一体机)", "product_description": "85英寸触摸显示屏内置计算机模块无线投屏",
             "ruling_number": "CN-2024-852852-001", "ruling_type": "CN_PRE_CLASSIFICATION", "issuing_authority": "中国海关总署",
             "ruling_date": date(2024, 3, 15), "expiry_date": date(2027, 3, 14),
             "decision": "归入85285200", "legal_basis": "归类总规则一及六", "classification_reasoning": "该产品兼具显示器和视频信号分配功能，主要功能为显示器，按监视器归入85285200",
             "key_factors": "带HDMI输入、VGA输入、触摸功能为附加功能不影响归类"},
            {"country": "CN", "hs_code": "84714190", "product_name": "工业控制计算机(工控机)", "product_description": "无风扇嵌入式工控机 Intel i7 8GB RAM 256GB SSD",
             "ruling_number": "CN-2024-847141-002", "ruling_type": "CN_PRE_CLASSIFICATION", "issuing_authority": "中国海关总署",
             "ruling_date": date(2024, 5, 20), "expiry_date": date(2027, 5, 19),
             "decision": "归入84714190", "legal_basis": "归类总规则一及六,第十六类注释五",
             "classification_reasoning": "该设备为自动数据处理设备，带有中央处理器和存储装置，符合税目8471描述",
             "key_factors": "带有VGA/HDMI/USB接口，使用Windows操作系统"},
            {"country": "CN", "hs_code": "85176299", "product_name": "5G CPE无线终端", "product_description": "5G无线路由器支持WiFi6 4个千兆LAN口",
             "ruling_number": "CN-2024-851762-003", "ruling_type": "CN_PRE_CLASSIFICATION", "issuing_authority": "中国海关总署",
             "ruling_date": date(2024, 8, 10), "expiry_date": date(2027, 8, 9),
             "decision": "归入85176299", "legal_basis": "归类总规则一及六", "classification_reasoning": "该设备为有线通信网络设备，用于信号接收转换传输，符合税目8517有线通信设备描述",
             "key_factors": "5G模块接入互联网，千兆LAN接口",
             "source_url": "http://www.customs.gov.cn/customs/302442/302445/index.html"},
            # 美国CBP预裁定
            {"country": "US", "hs_code": "85285900", "product_name": "Interactive Flat Panel Display", "product_description": "86-inch touch screen LCD display with built-in Android module",
             "ruling_number": "US-N345678-2023", "ruling_type": "US_CBP_RULING", "issuing_authority": "U.S. Customs and Border Protection",
             "ruling_date": date(2023, 11, 5), "expiry_date": date(2026, 11, 4),
             "decision": "Classified under 8528.59.00", "legal_basis": "GRI 1, 3(b); EN 84.71 vs 85.28",
             "classification_reasoning": "Primary function is display of images, not data processing. Touch functionality is subsidiary to display function.",
             "key_factors": "No keyboard, no mouse; HDMI/VGA primary inputs; Android is secondary function",
             "source_url": "https://rulings.cbp.gov/"},
            {"country": "US", "hs_code": "84713001", "product_name": "Tablet Computer with Keyboard", "product_description": "Detachable keyboard tablet PC 11-inch display Intel Core i5 8GB RAM",
             "ruling_number": "US-H876543-2024", "ruling_type": "US_CBP_RULING", "issuing_authority": "U.S. Customs and Border Protection",
             "ruling_date": date(2024, 1, 20), "expiry_date": date(2027, 1, 19),
             "decision": "Classified under 8471.30.01", "legal_basis": "GRI 1, Note 5(A) to Chapter 84",
             "classification_reasoning": "Portable digital ADP machine weighing less than 10kg with keyboard and display, meeting Note 5(A)(a) and (b) requirements",
             "key_factors": "Detachable but designed to work together as a portable unit",
             "source_url": "https://rulings.cbp.gov/"},
            # 欧盟预裁定
            {"country": "DE", "hs_code": "85284900", "product_name": "Laser Projector for Classroom", "product_description": "5000 lumens laser projector with HDMI/VGA/USB inputs",
             "ruling_number": "EU-EBTI-2024-00321", "ruling_type": "EU_EBTI", "issuing_authority": "European Commission",
             "ruling_date": date(2024, 6, 15), "expiry_date": date(2027, 6, 14),
             "decision": "Classified under 8528.49.00", "legal_basis": "GRI 1 and 6",
             "classification_reasoning": "Projector using laser light source for image projection, not capable of television reception, classified as other projection device",
             "key_factors": "No TV tuner, laser light source, primarily for educational use",
             "source_url": "https://ec.europa.eu/taxation_customs/ebti/"},
            {"country": "DE", "hs_code": "85414300", "product_name": "Photovoltaic Solar Panel", "product_description": "Monocrystalline silicon solar panel 550W 144 cells",
             "ruling_number": "EU-EBTI-2024-00452", "ruling_type": "EU_EBTI", "issuing_authority": "European Commission",
             "ruling_date": date(2024, 7, 1), "expiry_date": date(2027, 6, 30),
             "decision": "Classified under 8541.43.00", "legal_basis": "GRI 1 and 6",
             "classification_reasoning": "Photovoltaic cell assembled into panel, not elsewhere specified, classified as photosensitive semiconductor device",
             "key_factors": "Monocrystalline silicon cells, power output 550W, aluminum frame",
             "source_url": "https://ec.europa.eu/taxation_customs/ebti/"},
            # 越南预裁定
            {"country": "VN", "hs_code": "85285900", "product_name": "Màn hình LCD 75 inch", "product_description": "75-inch LCD display for digital signage without TV tuner",
             "ruling_number": "VN-GDC-2024-0089", "ruling_type": "CN_PRE_CLASSIFICATION", "issuing_authority": "Vietnam Customs (TCHQ)",
             "ruling_date": date(2024, 4, 10), "expiry_date": date(2027, 4, 9),
             "decision": "归入85285900", "legal_basis": "Quy tắc 1 và 6 GRI",
             "classification_reasoning": "显示设备不具备电视接收功能，作为监视器归入85285900",
             "key_factors": "无电视调谐器，用于广告展示"},
            # 日本预裁定
            {"country": "JP", "hs_code": "85258900", "product_name": "Industrial Camera Module", "product_description": "8MP industrial camera USB3.0 interface for machine vision",
             "ruling_number": "JP-2024-8525-0033", "ruling_type": "CN_PRE_CLASSIFICATION", "issuing_authority": "Japan Customs (税関)",
             "ruling_date": date(2024, 9, 1), "expiry_date": date(2027, 8, 31),
             "decision": "归类于85258900", "legal_basis": "GRI 1",
             "classification_reasoning": "数字照相机，非特种用途，按其他电视摄录设备归入85258900",
             "key_factors": "非特种相机，USB接口传输"},
        ]
        for r in rulings:
            db.add(HSRulingReference(**r))
        db.commit()
        logger.success(f"Seeded {len(rulings)} HS pre-rulings")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    seed_audit_logs()
    seed_hs_rulings()
    ensure_fts_indexes()
    yield
    logger.info("GTCS shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Global Trade Compliance System — 全球贸易通关决策平台",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION, "app": settings.APP_NAME}


# 前端静态文件服务
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(request: Request, full_path: str):
        fp = STATIC_DIR / full_path
        if fp.is_file():
            return FileResponse(str(fp))
        return FileResponse(str(STATIC_DIR / "index.html"))
