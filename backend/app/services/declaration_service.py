"""报关单 — 状态机 + 一致性检查 + CRUD

状态流转:
  draft → submitted → query_received → amended → cleared → closed
                   ↘                 ↗
                    ↳  ~~~~~~  ↲  (否->退回)
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Set
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_


# ─── State Machine ─────────────────────────────────────

STATES = ["draft", "submitted", "query_received", "amended", "cleared", "closed"]

VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "draft": {"submitted"},
    "submitted": {"query_received", "cleared", "draft"},
    "query_received": {"amended", "draft"},
    "amended": {"submitted", "cleared"},
    "cleared": {"closed"},
    "closed": set(),
}

TRANSITION_LABELS = {
    ("draft", "submitted"): "申报",
    ("submitted", "query_received"): "海关查询",
    ("submitted", "cleared"): "放行",
    ("submitted", "draft"): "退单",
    ("query_received", "amended"): "改单",
    ("query_received", "draft"): "退单重报",
    ("amended", "submitted"): "再次申报",
    ("amended", "cleared"): "审核放行",
    ("cleared", "closed"): "结关",
}


def validate_transition(current: str, target: str) -> bool:
    """Check if state transition is valid."""
    return target in VALID_TRANSITIONS.get(current, set())


def get_available_actions(status: str) -> List[Dict[str, str]]:
    """Get valid next actions for current status."""
    actions = []
    for target in VALID_TRANSITIONS.get(status, set()):
        label = TRANSITION_LABELS.get((status, target), target)
        actions.append({"action": target, "label": label})
    return actions


# ─── Consistency Checks ────────────────────────────────

def check_consistency(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run consistency checks on declaration items.

    Checks:
      1. HS code format validity
      2. Duplicate HS codes
      3. Missing required fields
      4. Unit price vs total price consistency
    """
    warnings = []
    errors = []
    hs_codes_seen: Set[str] = set()

    for i, item in enumerate(items):
        item_no = item.get("item_no", i + 1)
        hs = item.get("hs_code", "").replace(".", "").replace(" ", "")

        # HS code length check
        if len(hs) not in (6, 8, 10):
            warnings.append({
                "item_no": item_no,
                "field": "hs_code",
                "message": f"HS编码长度异常: {len(hs)}位 (标准6/8/10位)",
                "severity": "warning",
            })

        # Duplicate HS
        if hs in hs_codes_seen:
            warnings.append({
                "item_no": item_no,
                "field": "hs_code",
                "message": f"重复HS编码: {item.get('hs_code')}",
                "severity": "warning",
            })
        hs_codes_seen.add(hs)

        # Required fields
        if not item.get("name_cn"):
            errors.append({
                "item_no": item_no,
                "field": "name_cn",
                "message": "商品中文名称必填",
                "severity": "error",
            })

        # Price consistency
        qty = item.get("qty") or 0
        unit_price = item.get("unit_price") or 0
        total_price = item.get("total_price") or 0
        if qty > 0 and unit_price > 0:
            expected = round(qty * unit_price, 2)
            if abs(expected - total_price) > 0.01:
                warnings.append({
                    "item_no": item_no,
                    "field": "total_price",
                    "message": f"总价不一致: {qty}x{unit_price}={expected}, 填写{total_price}",
                    "severity": "warning",
                })

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ─── Declaration CRUD ──────────────────────────────────

from app.models.declaration import Declaration, DeclarationItem


def create_declaration(db: Session, data: Dict[str, Any]) -> Declaration:
    """Create a new draft declaration."""
    items_data = data.pop("items", [])

    declaration = Declaration(
        status="draft",
        **{k: v for k, v in data.items() if k in (
            "customs_no", "direction", "enterprise_id", "factory_id",
            "port_code", "trade_mode", "transport_mode", "currency",
            "total_value", "total_qty", "consignee", "consignor", "remark",
        )},
    )
    db.add(declaration)
    db.flush()

    for i, item_data in enumerate(items_data):
        item = DeclarationItem(
            declaration_id=declaration.id,
            item_no=i + 1,
            **{k: v for k, v in item_data.items() if k in (
                "product_id", "hs_code", "name_cn", "name_en",
                "qty", "unit", "unit_price", "total_price", "currency",
                "origin_country", "dest_country", "duty_rate", "duty_amount",
            )},
        )
        db.add(item)

    # Recalculate totals
    _recalc_totals(declaration, db)
    db.commit()
    db.refresh(declaration)
    return declaration


def _recalc_totals(declaration: Declaration, db: Session) -> None:
    """Recompute total_qty and total_value from items."""
    from sqlalchemy import func
    totals = db.query(
        func.coalesce(func.sum(DeclarationItem.qty), 0),
        func.coalesce(func.sum(DeclarationItem.total_price), 0),
    ).filter(DeclarationItem.declaration_id == declaration.id).first()
    declaration.total_qty = int(totals[0]) if totals else 0
    declaration.total_value = float(totals[1]) if totals else 0.0


def transition_declaration(
    db: Session, declaration_id: int, action: str, remark: Optional[str] = None
) -> Dict[str, Any]:
    """Transition declaration to a new state."""
    decl = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not decl:
        return {"error": "报关单不存在"}

    if not validate_transition(decl.status, action):
        return {
            "error": f"不允许的状态变更: {decl.status} → {action}",
            "current_status": decl.status,
            "valid_actions": [a["action"] for a in get_available_actions(decl.status)],
        }

    label = TRANSITION_LABELS.get((decl.status, action), action)
    decl.status = action
    if remark:
        decl.remark = (decl.remark or "") + f"\n[{label}] {remark}"
    db.commit()

    return {
        "id": decl.id,
        "declaration_no": decl.declaration_no,
        "from_status": decl.status,
        "new_status": action,
        "action_label": label,
    }


def get_declaration(db: Session, declaration_id: int) -> Optional[Dict[str, Any]]:
    """Get declaration with items."""
    decl = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not decl:
        return None

    items = db.query(DeclarationItem).filter(
        DeclarationItem.declaration_id == decl.id
    ).order_by(DeclarationItem.item_no).all()

    return {
        "id": decl.id,
        "declaration_no": decl.declaration_no,
        "customs_no": decl.customs_no,
        "direction": decl.direction,
        "status": decl.status,
        "enterprise_id": decl.enterprise_id,
        "port_code": decl.port_code,
        "trade_mode": decl.trade_mode,
        "transport_mode": decl.transport_mode,
        "currency": decl.currency,
        "total_value": decl.total_value,
        "total_qty": decl.total_qty,
        "consignee": decl.consignee,
        "consignor": decl.consignor,
        "remark": decl.remark,
        "available_actions": get_available_actions(decl.status),
        "items": [{
            "id": i.id,
            "item_no": i.item_no,
            "product_id": i.product_id,
            "hs_code": i.hs_code,
            "name_cn": i.name_cn,
            "name_en": i.name_en,
            "qty": i.qty,
            "unit": i.unit,
            "unit_price": i.unit_price,
            "total_price": i.total_price,
            "currency": i.currency,
            "origin_country": i.origin_country,
            "dest_country": i.dest_country,
            "duty_rate": i.duty_rate,
            "duty_amount": i.duty_amount,
        } for i in items],
    }


def list_declarations(
    db: Session,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    enterprise_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List declarations with filters."""
    q = db.query(Declaration)
    if status:
        q = q.filter(Declaration.status == status)
    if direction:
        q = q.filter(Declaration.direction == direction)
    if enterprise_id:
        q = q.filter(Declaration.enterprise_id == enterprise_id)

    total = q.count()
    offset = (page - 1) * page_size
    declarations = q.order_by(Declaration.id.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [{
            "id": d.id,
            "declaration_no": d.declaration_no,
            "direction": d.direction,
            "status": d.status,
            "total_value": d.total_value,
            "currency": d.currency,
            "consignee": d.consignee,
            "available_actions": get_available_actions(d.status),
            "created_at": str(d.created_at) if d.created_at else None,
        } for d in declarations],
    }


def check_before_submit(db: Session, declaration_id: int) -> Dict[str, Any]:
    """Run consistency checks before submission."""
    decl = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not decl:
        return {"passed": False, "error": "报关单不存在"}

    items = db.query(DeclarationItem).filter(
        DeclarationItem.declaration_id == decl.id
    ).all()

    # Convert to dict list for check_consistency
    item_dicts = [{
        "item_no": i.item_no,
        "hs_code": i.hs_code,
        "name_cn": i.name_cn,
        "qty": i.qty,
        "unit_price": i.unit_price,
        "total_price": i.total_price,
    } for i in items]

    consistency = check_consistency(item_dicts)

    # Additional checks
    checks = []

    # Basic field check
    if not decl.consignee:
        checks.append({"field": "consignee", "message": "收货人必填", "severity": "error"})
    if not decl.consignor:
        checks.append({"field": "consignor", "message": "发货人必填", "severity": "error"})
    if not decl.direction:
        checks.append({"field": "direction", "message": "进出口方向必填", "severity": "error"})

    if not items:
        checks.append({"field": "items", "message": "至少需要一个报关项", "severity": "error"})

    all_errors = consistency["errors"] + [c for c in checks if c["severity"] == "error"]
    all_warnings = consistency["warnings"] + [c for c in checks if c["severity"] == "warning"]

    return {
        "passed": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
    }
