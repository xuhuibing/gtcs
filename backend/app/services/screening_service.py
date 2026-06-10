from __future__ import annotations
"""受限制方筛查引擎 — 模糊匹配 + 名单管理"""
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
from datetime import date
import json
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.screening import ScreeningList, ScreeningLog


def _normalize(text: str) -> str:
    """标准化待匹配文本：去空格、去标点、转大写"""
    import re
    t = text.upper()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _token_sort_ratio(a: str, b: str) -> float:
    """排序后比较的相似度（忽略词序）"""
    a_tokens = sorted(_normalize(a).split())
    b_tokens = sorted(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    a_str = " ".join(a_tokens)
    b_str = " ".join(b_tokens)
    return SequenceMatcher(None, a_str, b_str).ratio() * 100


def _partial_ratio(a: str, b: str) -> float:
    """短字符串在长字符串中的最佳匹配"""
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if len(a_norm) <= len(b_norm):
        short, long = a_norm, b_norm
    else:
        short, long = b_norm, a_norm

    best = 0
    short_len = len(short)
    if short_len == 0:
        return 0.0
    for i in range(len(long) - short_len + 1):
        ratio = SequenceMatcher(None, short, long[i:i + short_len]).ratio() * 100
        if ratio > best:
            best = ratio
    return best


def match_name(name: str, threshold: float = 60.0) -> dict:
    """对单个名字进行模糊匹配，返回匹配结果和分数"""
    return {
        "name": name,
        "keywords": _normalize(name).split(),
    }


def screen_name(
    db: Session,
    name: str,
    list_types: Optional[List[str]] = None,
    min_score: float = 60.0,
) -> List[Dict[str, Any]]:
    """筛查一个名字，返回匹配结果（分数从高到低）"""
    norm = _normalize(name)
    tokens = norm.split()
    if not tokens:
        return []

    q = db.query(ScreeningList).filter(ScreeningList.status == "ACTIVE")
    keywords = " ".join(tokens[:5])  # 最多用5个关键词

    # 用 OR 模糊搜索名字和别名
    filters = [
        ScreeningList.name.ilike(f"%{t}%")
        for t in tokens[:3]
    ]
    filters.append(ScreeningList.name_cn.ilike(f"%{keywords}%"))
    q = q.filter(or_(*filters))

    if list_types:
        q = q.filter(ScreeningList.list_type.in_(list_types))

    candidates = q.limit(200).all()

    results = []
    for candidate in candidates:
        # 主名字匹配
        main_score = _token_sort_ratio(name, candidate.name)
        cn_score = _token_sort_ratio(name, candidate.name_cn or "") if candidate.name_cn else 0
        alias_scores = []
        if candidate.alias:
            try:
                aliases = json.loads(candidate.alias) if isinstance(candidate.alias, str) else candidate.alias
                for alias in aliases:
                    alias_scores.append(_token_sort_ratio(name, alias))
            except (json.JSONDecodeError, TypeError):
                pass

        best_score = max(main_score, cn_score, max(alias_scores) if alias_scores else 0)
        best_field = "name"
        if best_score == cn_score and cn_score > main_score:
            best_field = "name_cn"
        elif alias_scores and best_score == max(alias_scores):
            best_field = "alias"

        if best_score >= min_score:
            results.append({
                "match_id": candidate.id,
                "list_type": candidate.list_type,
                "id_type": candidate.id_type,
                "match_name": candidate.name,
                "match_name_cn": candidate.name_cn,
                "country": candidate.country,
                "program": candidate.program,
                "reason": candidate.reason,
                "score": round(best_score, 1),
                "match_field": best_field,
                "effective_date": str(candidate.effective_date) if candidate.effective_date else None,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def screen_batch(
    db: Session,
    names: List[str],
    list_types: Optional[List[str]] = None,
    min_score: float = 60.0,
) -> List[Dict[str, Any]]:
    """批量筛查多个名字"""
    results = []
    for name in names:
        matches = screen_name(db, name, list_types, min_score)
        results.append({
            "screened_name": name,
            "match_count": len(matches),
            "risk_level": _get_risk_level(matches),
            "matches": matches,
        })
    return results


def _get_risk_level(matches: list) -> str:
    """根据匹配结果确定风险等级"""
    if not matches:
        return "CLEAN"
    best = max(m["score"] for m in matches)
    if best >= 90:
        return "HIGH"
    elif best >= 75:
        return "MEDIUM"
    else:
        return "LOW"


def log_screening(
    db: Session,
    screened_name: str,
    screened_type: str,
    matches: list,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    screened_by: Optional[str] = None,
) -> ScreeningLog:
    """记录筛查到日志"""
    log = ScreeningLog(
        screened_by=screened_by or "SYSTEM",
        screened_name=screened_name,
        screened_type=screened_type,
        match_count=len(matches),
        risk_level=_get_risk_level(matches),
        match_details=json.dumps(matches, ensure_ascii=False) if matches else None,
        reference_id=reference_id,
        reference_type=reference_type,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_screening_lists(db: Session) -> list:
    """获取所有制裁名单类型统计"""
    from sqlalchemy import func
    results = (
        db.query(
            ScreeningList.list_type,
            func.count(ScreeningList.id).label("count"),
        )
        .filter(ScreeningList.status == "ACTIVE")
        .group_by(ScreeningList.list_type)
        .all()
    )
    return [{"list_type": r.list_type, "count": r.count} for r in results]


def get_screening_logs(
    db: Session,
    limit: int = 50,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
) -> list:
    """获取筛查记录"""
    q = db.query(ScreeningLog)
    if risk_level:
        q = q.filter(ScreeningLog.risk_level == risk_level)
    if status:
        q = q.filter(ScreeningLog.status == status)
    logs = q.order_by(ScreeningLog.id.desc()).limit(limit).all()

    return [{
        "id": l.id,
        "screened_by": l.screened_by,
        "screened_name": l.screened_name,
        "screened_type": l.screened_type,
        "match_count": l.match_count,
        "risk_level": l.risk_level,
        "reference_id": l.reference_id,
        "reference_type": l.reference_type,
        "status": l.status,
        "reviewed_by": l.reviewed_by,
        "review_result": l.review_result,
        "created_at": str(l.created_at) if l.created_at else None,
    } for l in logs]
