"""Actionable insights generator for follow-on investment candidates.

Analyzes score_details + growth_metrics to produce ranked recommendations
on what data/info is needed to make a company an attractive follow-on target.
"""
from __future__ import annotations

import json
from typing import Optional


# Maps growth metric fields → scoring factor, max points, Korean label
FIELD_SCORING_MAP = {
    "mrr_growth_rate_pct": {
        "factor": "growth_velocity",
        "max_points": 15,
        "label": "MRR 성장률 데이터 필요",
        "detail": "입력 시 최대 15점 추가 가능",
    },
    "revenue_multiple": {
        "factor": "growth_velocity",
        "max_points": 10,
        "label": "매출 배수 데이터 필요",
        "detail": "첫 미팅 대비 현재 매출로 최대 10점 가능",
        "check_fields": ["monthly_revenue", "revenue_at_first_meeting"],
    },
    "ndr_pct": {
        "factor": "growth_velocity",
        "max_points": 5,
        "label": "NDR 데이터 필요",
        "detail": "입력 시 최대 5점 추가 가능",
    },
    "monthly_burn": {
        "factor": "capital_efficiency",
        "max_points": 10,
        "label": "월 번 데이터 필요",
        "detail": "번 멀티플 계산을 위해 필요",
    },
    "headcount": {
        "factor": "capital_efficiency",
        "max_points": 5,
        "label": "인원 데이터 필요",
        "detail": "인당 매출 계산을 위해 필요",
    },
    "paying_customers": {
        "factor": "capital_efficiency",
        "max_points": 5,
        "label": "유료 고객 수 필요",
        "detail": "입력 시 최대 5점 추가 가능",
    },
    "runway_months": {
        "factor": "funding_urgency",
        "max_points": 12,
        "label": "런웨이 데이터 필요",
        "detail": "펀딩 타이밍 점수 개선 가능",
        "check_fields": ["runway_months", "cash_on_hand"],
    },
    "last_funding_date": {
        "factor": "funding_urgency",
        "max_points": 8,
        "label": "최근 펀딩 일자 필요",
        "detail": "입력 시 최대 8점 추가 가능",
    },
}

# Labels for low-score factor recommendations
FACTOR_LABELS = {
    "growth_velocity": "성장 속도 점수 낮음 — 매출/성장 데이터 업데이트 권장",
    "capital_efficiency": "자본 효율성 점수 낮음 — 번/매출/고객 데이터 확인 필요",
    "funding_urgency": "펀딩 타이밍 점수 낮음 — 런웨이/펀딩 정보 업데이트 필요",
    "deal_status": "딜 상태가 '최종탈락' — '트래킹'으로 변경 시 +8점",
    "comments": "투자 코멘트 추가 필요 — 코멘트 기반 점수 향상 가능",
    "stage_valuation": "단계/밸류에이션 점수 낮음 — 최신 정보 반영 필요",
}


def _priority(points: int) -> str:
    if points >= 10:
        return "high"
    if points >= 5:
        return "medium"
    return "low"


def generate_action_items(
    score_details_json: Optional[str],
    growth_data,
    comment_count: int,
) -> list[dict]:
    """Generate ranked action items for a company.

    Args:
        score_details_json: JSON string from Company.score_details
        growth_data: latest GrowthMetrics ORM object (or None)
        comment_count: number of investment comments
    Returns:
        Sorted list of action item dicts
    """
    items: list[dict] = []

    # Parse score_details
    details: dict = {}
    if score_details_json:
        try:
            details = json.loads(score_details_json)
        except (json.JSONDecodeError, TypeError):
            pass

    # --- Phase A: Missing data analysis ---
    if growth_data is None:
        items.append({
            "type": "opportunity",
            "field": "growth_data",
            "potential_points": 50,
            "label": "성장 데이터 입력 필요",
            "detail": "성장/효율/펀딩 점수 산출을 위해 데이터 업로드 필요",
            "priority": "high",
            "factor": "all",
        })
    else:
        for field_key, config in FIELD_SCORING_MAP.items():
            is_missing = False

            if "check_fields" in config:
                if field_key == "revenue_multiple":
                    is_missing = (
                        not getattr(growth_data, "monthly_revenue", None)
                        or not getattr(growth_data, "revenue_at_first_meeting", None)
                    )
                elif field_key == "runway_months":
                    runway = getattr(growth_data, "runway_months", None)
                    cash = getattr(growth_data, "cash_on_hand", None)
                    burn = getattr(growth_data, "monthly_burn", None)
                    is_missing = runway is None and not (cash and burn)
            else:
                is_missing = getattr(growth_data, field_key, None) is None

            if is_missing:
                items.append({
                    "type": "missing_data",
                    "field": field_key,
                    "potential_points": config["max_points"],
                    "label": config["label"],
                    "detail": config["detail"],
                    "priority": _priority(config["max_points"]),
                    "factor": config["factor"],
                })

    # --- Phase B: Low-score factor analysis ---
    factors_with_missing = {i["factor"] for i in items if i["type"] == "missing_data"}

    for factor_key in ["growth_velocity", "capital_efficiency", "funding_urgency",
                        "deal_status", "comments", "stage_valuation"]:
        factor_data = details.get(factor_key)
        if not factor_data or not isinstance(factor_data, dict):
            continue

        value = factor_data.get("value", 0)
        max_val = factor_data.get("max", 10)
        gap = max_val - value

        # Skip if already covered by missing_data for same factor
        if factor_key in factors_with_missing:
            continue

        # Deal status: only flag if it's 최종탈락
        if factor_key == "deal_status" and value <= 2:
            items.append({
                "type": "opportunity",
                "field": "deal_status",
                "potential_points": 8,
                "label": FACTOR_LABELS[factor_key],
                "detail": "'트래킹' 상태로 변경하면 점수 크게 향상",
                "priority": "medium",
                "factor": factor_key,
            })
            continue

        # Comments with low count
        if factor_key == "comments" and comment_count < 3 and value < 7:
            items.append({
                "type": "low_score",
                "field": "comments",
                "potential_points": gap,
                "label": FACTOR_LABELS[factor_key],
                "detail": f"현재 {comment_count}개 → 추가 코멘트로 점수 개선 가능",
                "priority": _priority(gap),
                "factor": factor_key,
            })
            continue

        # General low-score: flag if gap > 30% of max
        if gap > max_val * 0.3:
            items.append({
                "type": "low_score",
                "field": factor_key,
                "potential_points": gap,
                "label": FACTOR_LABELS[factor_key],
                "detail": f"현재 {value}/{max_val}점",
                "priority": _priority(gap),
                "factor": factor_key,
            })

    # --- Phase C: Special opportunities ---
    if comment_count == 0 and not any(i["field"] == "comments" for i in items):
        items.append({
            "type": "opportunity",
            "field": "comments",
            "potential_points": 5,
            "label": "첫 투자 코멘트 추가 필요",
            "detail": "코멘트 작성 시 점수에 반영됨",
            "priority": "medium",
            "factor": "comments",
        })

    # Sort by potential_points desc, then priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: (-x["potential_points"], priority_order.get(x["priority"], 2)))

    return items


def get_top_action_items(items: list[dict], n: int = 2) -> list[dict]:
    """Return the top N action items for dashboard card display."""
    return items[:n]
