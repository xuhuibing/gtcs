from __future__ import annotations
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.price_risk import PriceRecord, PriceBaseline, PriceAlert, PriceJustification


def create_price_record(db: Session, data: dict) -> PriceRecord:
    unit_price_usd = data.get("unit_price_usd")
    if unit_price_usd is None and data.get("currency") == "USD":
        unit_price_usd = data["unit_price"]

    record = PriceRecord(
        product_code=data.get("product_code"),
        product_name=data.get("product_name"),
        brand=data.get("brand"),
        model=data.get("model"),
        hs_code=data["hs_code"],
        specifications=data.get("specifications"),
        direction=data.get("direction", "IMPORT"),
        origin_country=data.get("origin_country"),
        dest_country=data.get("dest_country"),
        unit_price=Decimal(str(data["unit_price"])),
        currency=data.get("currency", "USD"),
        unit_price_usd=Decimal(str(unit_price_usd)) if unit_price_usd else None,
        price_term=data.get("price_term"),
        quantity=Decimal(str(data["quantity"])) if data.get("quantity") else None,
        total_value=Decimal(str(data["total_value"])) if data.get("total_value") else None,
        unit=data.get("unit"),
        buyer=data.get("buyer"),
        seller=data.get("seller"),
        is_related_party=data.get("is_related_party", False),
        declaration_no=data.get("declaration_no"),
        invoice_no=data.get("invoice_no"),
        contract_no=data.get("contract_no"),
        shipment_date=data.get("shipment_date"),
        declaration_date=data.get("declaration_date") or date.today(),
    )
    db.add(record)
    db.flush()

    alerts = check_price_against_baseline(db, record)
    if alerts:
        record.risk_flag = alerts[0].severity
        record.risk_reason = alerts[0].risk_description
    else:
        record.risk_flag = "NORMAL"

    db.commit()
    return record


def check_price_against_baseline(db: Session, record: PriceRecord) -> List[PriceAlert]:
    baseline = find_baseline(db, record)
    if not baseline:
        return []

    alerts = []
    price = record.unit_price_usd or record.unit_price

    if baseline.alert_low_price and price < baseline.alert_low_price:
        deviation_pct = ((baseline.avg_price - price) / baseline.avg_price * 100) if baseline.avg_price else Decimal("0")
        alert = PriceAlert(
            price_record_id=record.id,
            baseline_id=baseline.id,
            alert_type="BELOW_FLOOR",
            current_price=price,
            baseline_price=baseline.avg_price,
            deviation_pct=-deviation_pct,
            deviation_amount=price - baseline.avg_price,
            severity="HIGH" if deviation_pct > 30 else "MEDIUM",
            risk_description=f"单价 {price} 低于预警下限 {baseline.alert_low_price}，偏离均价 {deviation_pct:.1f}%",
            customs_implication="海关可能质疑低报价格，启动价格磋商或审价程序",
            suggested_action="准备价格合理性说明材料（批量折扣/促销/型号差异等）",
            status="PENDING",
        )
        db.add(alert)
        alerts.append(alert)

    if baseline.alert_high_price and price > baseline.alert_high_price:
        deviation_pct = ((price - baseline.avg_price) / baseline.avg_price * 100) if baseline.avg_price else Decimal("0")
        alert = PriceAlert(
            price_record_id=record.id,
            baseline_id=baseline.id,
            alert_type="ABOVE_CEILING",
            current_price=price,
            baseline_price=baseline.avg_price,
            deviation_pct=deviation_pct,
            deviation_amount=price - baseline.avg_price,
            severity="MEDIUM",
            risk_description=f"单价 {price} 高于预警上限 {baseline.alert_high_price}，偏离均价 {deviation_pct:.1f}%",
            customs_implication="出口方向高价可能涉及多付汇/转移定价审查",
            suggested_action="核查是否涉及特许权使用费、协助费用应分摊入完税价格",
            status="PENDING",
        )
        db.add(alert)
        alerts.append(alert)

    prev_record = db.query(PriceRecord).filter(
        PriceRecord.id != record.id,
        PriceRecord.hs_code == record.hs_code,
        PriceRecord.brand == record.brand,
        PriceRecord.model == record.model,
        PriceRecord.direction == record.direction,
    ).order_by(desc(PriceRecord.declaration_date)).first()

    if prev_record and baseline.alert_change_pct:
        prev_price = prev_record.unit_price_usd or prev_record.unit_price
        if prev_price and prev_price > 0:
            change_pct = abs((price - prev_price) / prev_price * 100)
            if change_pct > baseline.alert_change_pct:
                direction = "SUDDEN_SPIKE" if price > prev_price else "SUDDEN_DROP"
                alert = PriceAlert(
                    price_record_id=record.id,
                    baseline_id=baseline.id,
                    alert_type=direction,
                    current_price=price,
                    baseline_price=baseline.avg_price,
                    deviation_pct=change_pct if price > prev_price else -change_pct,
                    deviation_amount=price - prev_price,
                    previous_price=prev_price,
                    previous_date=prev_record.declaration_date,
                    severity="HIGH" if change_pct > 50 else "MEDIUM",
                    risk_description=f"与上一票价格 {prev_price} 相比变动 {change_pct:.1f}%",
                    customs_implication="海关可能要求解释价格剧烈波动原因",
                    suggested_action="提供价格变动原因说明及佐证材料",
                    status="PENDING",
                )
                db.add(alert)
                alerts.append(alert)

    db.flush()
    return alerts


def find_baseline(db: Session, record: PriceRecord) -> PriceBaseline | None:
    q = db.query(PriceBaseline).filter(
        PriceBaseline.hs_code == record.hs_code,
        PriceBaseline.direction == record.direction,
    )
    if record.brand:
        q = q.filter(PriceBaseline.brand == record.brand)
    if record.model:
        q = q.filter(PriceBaseline.model == record.model)

    baseline = q.first()
    if not baseline:
        baseline = db.query(PriceBaseline).filter(
            PriceBaseline.hs_code == record.hs_code,
            PriceBaseline.direction == record.direction,
            PriceBaseline.brand == None,
            PriceBaseline.model == None,
        ).first()
    return baseline


def recalculate_baseline(db: Session, hs_code: str, direction: str = "IMPORT",
                         brand: str = None, model: str = None) -> PriceBaseline | None:
    q = db.query(PriceRecord).filter(
        PriceRecord.hs_code == hs_code,
        PriceRecord.direction == direction,
        PriceRecord.risk_flag != "BLOCKED",
    )
    if brand:
        q = q.filter(PriceRecord.brand == brand)
    if model:
        q = q.filter(PriceRecord.model == model)

    lookback = date.today() - timedelta(days=365)
    q = q.filter(PriceRecord.declaration_date >= lookback)

    records = q.all()
    if not records:
        return None

    prices = [float(r.unit_price_usd or r.unit_price) for r in records if r.unit_price]
    if not prices:
        return None

    import statistics
    avg = statistics.mean(prices)
    std = statistics.stdev(prices) if len(prices) > 1 else 0
    med = statistics.median(prices)

    existing = db.query(PriceBaseline).filter(
        PriceBaseline.hs_code == hs_code,
        PriceBaseline.direction == direction,
        PriceBaseline.brand == brand,
        PriceBaseline.model == model,
    ).first()

    if existing:
        baseline = existing
    else:
        baseline = PriceBaseline(hs_code=hs_code, direction=direction, brand=brand, model=model)
        db.add(baseline)

    baseline.avg_price = Decimal(str(round(avg, 4)))
    baseline.min_price = Decimal(str(round(min(prices), 4)))
    baseline.max_price = Decimal(str(round(max(prices), 4)))
    baseline.std_deviation = Decimal(str(round(std, 4)))
    baseline.median_price = Decimal(str(round(med, 4)))
    baseline.sample_count = len(prices)
    baseline.alert_low_price = Decimal(str(round(avg - 2 * std, 4))) if std > 0 else Decimal(str(round(avg * 0.7, 4)))
    baseline.alert_high_price = Decimal(str(round(avg + 2 * std, 4))) if std > 0 else Decimal(str(round(avg * 1.5, 4)))
    baseline.alert_change_pct = Decimal("30")
    baseline.threshold_source = "AUTO"
    baseline.last_calculated = datetime.now()
    baseline.valid_from = lookback
    baseline.valid_to = date.today() + timedelta(days=90)

    db.commit()
    return baseline


def get_price_history(db: Session, hs_code: str, brand: str = None,
                      model: str = None, limit: int = 50) -> List[dict]:
    q = db.query(PriceRecord).filter(PriceRecord.hs_code == hs_code)
    if brand:
        q = q.filter(PriceRecord.brand == brand)
    if model:
        q = q.filter(PriceRecord.model == model)

    records = q.order_by(desc(PriceRecord.declaration_date)).limit(limit).all()

    return [{
        "id": r.id,
        "product_name": r.product_name,
        "brand": r.brand,
        "model": r.model,
        "unit_price": r.unit_price,
        "unit_price_usd": r.unit_price_usd,
        "currency": r.currency,
        "declaration_date": str(r.declaration_date) if r.declaration_date else None,
        "origin_country": r.origin_country,
        "dest_country": r.dest_country,
        "risk_flag": r.risk_flag,
        "declaration_no": r.declaration_no,
    } for r in records]


def get_alerts(db: Session, status: str = None, severity: str = None, limit: int = 50) -> List[dict]:
    q = db.query(PriceAlert)
    if status:
        q = q.filter(PriceAlert.status == status)
    if severity:
        q = q.filter(PriceAlert.severity == severity)

    alerts = q.order_by(desc(PriceAlert.triggered_at)).limit(limit).all()

    return [{
        "id": a.id,
        "alert_type": a.alert_type,
        "current_price": a.current_price,
        "baseline_price": a.baseline_price,
        "deviation_pct": a.deviation_pct,
        "severity": a.severity,
        "risk_description": a.risk_description,
        "customs_implication": a.customs_implication,
        "suggested_action": a.suggested_action,
        "status": a.status,
        "triggered_at": str(a.triggered_at) if a.triggered_at else None,
    } for a in alerts]
