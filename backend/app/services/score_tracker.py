from __future__ import annotations
"""Score history tracking — logs every score change with analysis.

Compares old vs new factor breakdowns to explain WHY a score changed,
and generates Korean meta-insights about the investment signal.
"""
import json
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.score_history import ScoreHistory

# Factor display names (Korean)
FACTOR_LABELS = {
    "growth_velocity": "성장 속도",
    "capital_efficiency": "자본 효율성",
    "funding_urgency": "펀딩 시급성",
    "deal_status": "딜 상태",
    "comments": "코멘트 시그널",
    "stage_valuation": "스테이지 & 밸류에이션",
}


def record_score_change(
    company: Company,
    new_color: str,
    new_value: int,
    new_details_json: str,
    trigger_type: str = "unknown",
    trigger_detail: str = "",
    db: Session = None,
) -> ScoreHistory | None:
    """Record a score snapshot and analyze changes from the previous score.

    Returns the created ScoreHistory row, or None if db is not provided.
    """
    if db is None:
        return None

    old_color = company.traffic_score or "red"
    old_value = company.score_value or 0
    old_details_json = company.score_details

    delta = new_value - old_value

    # Analyze what changed between factor breakdowns
    change_reasons = _analyze_changes(old_details_json, new_details_json)
    meta_insight = _generate_meta_insight(
        company.company_name, old_color, new_color, old_value, new_value,
        delta, change_reasons,
    )

    entry = ScoreHistory(
        company_id=company.id,
        score_value=new_value,
        traffic_score=new_color,
        score_details=new_details_json,
        previous_score_value=old_value,
        previous_traffic_score=old_color,
        score_change=delta,
        change_reasons=json.dumps(change_reasons, ensure_ascii=False),
        meta_insight=meta_insight,
        trigger_type=trigger_type,
        trigger_detail=trigger_detail,
    )
    db.add(entry)
    return entry


def _analyze_changes(old_json: str | None, new_json: str | None) -> list[dict]:
    """Compare two score_details JSON strings and return a list of change reasons."""
    reasons = []

    old = _safe_parse(old_json)
    new = _safe_parse(new_json)

    if not new:
        return reasons

    factors = ["growth_velocity", "capital_efficiency", "funding_urgency",
               "deal_status", "comments", "stage_valuation"]

    for factor in factors:
        old_factor = old.get(factor, {}) if old else {}
        new_factor = new.get(factor, {})

        old_val = old_factor.get("value", 0) if isinstance(old_factor, dict) else 0
        new_val = new_factor.get("value", 0) if isinstance(new_factor, dict) else 0
        max_val = new_factor.get("max", 0) if isinstance(new_factor, dict) else 0
        label = new_factor.get("label", "") if isinstance(new_factor, dict) else ""

        delta = new_val - old_val

        if delta != 0:
            reasons.append({
                "factor": factor,
                "factor_label": FACTOR_LABELS.get(factor, factor),
                "old_value": old_val,
                "new_value": new_val,
                "max_value": max_val,
                "delta": delta,
                "direction": "up" if delta > 0 else "down",
                "detail": label,
            })

    # Check data completeness change
    old_completeness = old.get("data_completeness", 0) if old else 0
    new_completeness = new.get("data_completeness", 0)
    if new_completeness != old_completeness:
        reasons.append({
            "factor": "data_completeness",
            "factor_label": "데이터 완성도",
            "old_value": old_completeness,
            "new_value": new_completeness,
            "delta": round(new_completeness - old_completeness, 1),
            "direction": "up" if new_completeness > old_completeness else "down",
            "detail": f"{new_completeness}%",
        })

    return reasons


def _generate_meta_insight(
    company_name: str,
    old_color: str,
    new_color: str,
    old_value: int,
    new_value: int,
    delta: int,
    change_reasons: list[dict],
) -> str:
    """Generate a Korean meta-insight about the score change."""
    if not change_reasons and delta == 0:
        return f"{company_name}: 점수 변동 없음 ({new_value}점, {_color_kr(new_color)})"

    # Color transition
    color_changed = old_color != new_color
    parts = []

    if color_changed:
        parts.append(
            f"신호등 변경: {_color_kr(old_color)} → {_color_kr(new_color)}"
        )

    if delta > 0:
        parts.append(f"점수 +{delta}점 상승 ({old_value} → {new_value})")
    elif delta < 0:
        parts.append(f"점수 {delta}점 하락 ({old_value} → {new_value})")
    else:
        parts.append(f"점수 유지 ({new_value}점)")

    # Top factors that changed
    sorted_reasons = sorted(change_reasons, key=lambda r: abs(r.get("delta", 0)), reverse=True)
    factor_changes = [r for r in sorted_reasons if r["factor"] != "data_completeness"]

    if factor_changes:
        top = factor_changes[:3]
        factor_parts = []
        for r in top:
            d = r["delta"]
            sign = "+" if d > 0 else ""
            factor_parts.append(f"{r['factor_label']} {sign}{d}점")
        parts.append("주요 변동: " + ", ".join(factor_parts))

    # Data completeness note
    data_change = next((r for r in change_reasons if r["factor"] == "data_completeness"), None)
    if data_change and data_change["delta"] > 0:
        parts.append(f"데이터 완성도 향상 ({data_change['detail']})")

    # Investment signal interpretation
    if new_value >= 55 and old_value < 55:
        parts.append("⚡ 후속 투자 검토 권장 구간 진입")
    elif new_value < 30 and old_value >= 30:
        parts.append("⚠️ 모니터링 구간에서 홀드 구간으로 하락")
    elif new_value >= 55:
        parts.append("📈 후속 투자 검토 구간 유지")
    elif new_value >= 30:
        parts.append("👀 모니터링 구간")

    return f"{company_name}: " + " | ".join(parts)


def _color_kr(color: str) -> str:
    return {"green": "🟢 검토", "yellow": "🟡 모니터", "red": "🔴 홀드"}.get(color, color)


def _safe_parse(json_str: str | None) -> dict | None:
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None
