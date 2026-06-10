from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.declaration_service import (
    create_declaration, get_declaration, list_declarations,
    transition_declaration, check_before_submit, check_consistency,
    get_available_actions,
)

router = APIRouter(prefix="/declaration", tags=["报关单"])


@router.post("/create")
def create(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    try:
        decl = create_declaration(db, data)
        return get_declaration(db, decl.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
def list_all(
    status: Optional[str] = None,
    direction: Optional[str] = None,
    enterprise_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    return list_declarations(db, status, direction, enterprise_id, page, page_size)


@router.get("/{declaration_id}")
def get(declaration_id: int, db: Session = Depends(get_db)):
    result = get_declaration(db, declaration_id)
    if not result:
        raise HTTPException(status_code=404, detail="报关单不存在")
    return result


@router.post("/{declaration_id}/transition")
def transition(
    declaration_id: int,
    action: str = Query(...),
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
):
    result = transition_declaration(db, declaration_id, action, remark)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{declaration_id}/actions")
def available_actions(declaration_id: int, db: Session = Depends(get_db)):
    """Get available transition actions for a declaration."""
    from app.models.declaration import Declaration
    decl = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="报关单不存在")
    return {
        "id": decl.id,
        "status": decl.status,
        "available_actions": get_available_actions(decl.status),
    }


@router.post("/{declaration_id}/check")
def pre_submit_check(declaration_id: int, db: Session = Depends(get_db)):
    """Run consistency checks before submission."""
    return check_before_submit(db, declaration_id)


@router.post("/consistency/check")
def consistency_check(
    items: List[Dict[str, Any]] = Body(...),
):
    """Standalone consistency check for declaration items."""
    return check_consistency(items)
