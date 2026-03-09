from __future__ import annotations
"""Growth-focused scoring engine for follow-on investment candidates.

Score range: 0-100
- Green (>=55): Review Now
- Yellow (>=30): Monitor
- Red (<30): Hold

6 Factors:
  Growth Velocity       (30 pts) — MRR growth, revenue multiple, NDR
  Capital Efficiency    (20 pts) — Burn multiple, rev/headcount, customers
  Funding Timing        (20 pts) — Runway urgency, time since last round
  Deal Status           (10 pts) — 트래킹 vs 최종탈락
  Comment Signals       (10 pts) — Keyword sentiment
  Stage & Valuation Fit (10 pts) — Stage fit + valuation attractiveness
"""
import json
import re
from datetime import datetime, timezone


def compute_traffic_score(company, comments: list, growth_data=None) -> tuple:
    """Compute growth-focused traffic light score.

    Args:
        company: Company ORM object
        comments: list of InvestmentComment objects
        growth_data: latest GrowthMetrics ORM object (or None)

    Returns: (traffic_color, score_value, score_details_json)
    """
    details = {}

    # Factor 1: Growth Velocity (30 pts)
    gv = _compute_growth_velocity(growth_data)
    details["growth_velocity"] = gv

    # Factor 2: Capital Efficiency (20 pts)
    ce = _compute_capital_efficiency(growth_data)
    details["capital_efficiency"] = ce

    # Factor 3: Funding Timing (20 pts)
    ft = _compute_funding_urgency(growth_data)
    details["funding_urgency"] = ft

    # Factor 4: Deal Status (10 pts)
    status_val = 10 if company.deal_status == "트래킹" else 2
    details["deal_status"] = {"value": status_val, "max": 10, "label": company.deal_status or "unknown"}

    # Factor 5: Comment Signals (10 pts)
    comment_texts = [c.comment_text for c in comments] if comments else []
    comment_val = _compute_comment_score(comment_texts)
    details["comments"] = {"value": comment_val, "max": 10, "label": f"{len(comment_texts)} comments"}

    # Factor 6: Stage & Valuation Fit (10 pts)
    sv = _compute_stage_valuation(company)
    details["stage_valuation"] = sv

    total = (gv["value"] + ce["value"] + ft["value"]
             + status_val + comment_val + sv["value"])
    details["total"] = total

    # Data completeness
    completeness = _compute_data_completeness(growth_data)
    details["data_completeness"] = completeness
    details["has_growth_data"] = growth_data is not None

    if total >= 55:
        color = "green"
    elif total >= 30:
        color = "yellow"
    else:
        color = "red"

    return color, total, json.dumps(details, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Factor 1: Growth Velocity (30 pts)
# ---------------------------------------------------------------------------
def _compute_growth_velocity(gd) -> dict:
    if gd is None:
        return {"value": 0, "max": 30, "label": "데이터 없음"}

    score = 0
    parts = []

    # 1a: MRR Growth Rate (15 pts)
    if gd.mrr_growth_rate_pct is not None:
        rate = gd.mrr_growth_rate_pct
        if rate >= 20:
            score += 15
        elif rate >= 15:
            score += 13
        elif rate >= 10:
            score += 10
        elif rate >= 5:
            score += 6
        elif rate >= 0:
            score += 2
        parts.append(f"MRR +{rate:.0f}%")

    # 1b: Revenue multiple since first meeting (10 pts)
    if (gd.monthly_revenue and gd.revenue_at_first_meeting
            and gd.revenue_at_first_meeting > 0):
        multiple = gd.monthly_revenue / gd.revenue_at_first_meeting
        if multiple >= 5:
            score += 10
        elif multiple >= 3:
            score += 8
        elif multiple >= 2:
            score += 6
        elif multiple >= 1.5:
            score += 4
        elif multiple >= 1:
            score += 2
        parts.append(f"{multiple:.1f}x since meeting")

    # 1c: NDR / PMF signal (5 pts)
    if gd.ndr_pct is not None:
        if gd.ndr_pct >= 130:
            score += 5
        elif gd.ndr_pct >= 120:
            score += 4
        elif gd.ndr_pct >= 110:
            score += 3
        elif gd.ndr_pct >= 100:
            score += 2
        parts.append(f"NDR {gd.ndr_pct:.0f}%")

    return {"value": min(score, 30), "max": 30, "label": ", ".join(parts) or "일부 데이터"}


# ---------------------------------------------------------------------------
# Factor 2: Capital Efficiency & Burn (20 pts)
# ---------------------------------------------------------------------------
def _compute_capital_efficiency(gd) -> dict:
    if gd is None:
        return {"value": 0, "max": 20, "label": "데이터 없음"}

    score = 0
    parts = []

    # 2a: Burn multiple (10 pts)
    if gd.monthly_burn and gd.mrr and gd.mrr_growth_rate_pct and gd.mrr_growth_rate_pct > 0:
        net_new_mrr = gd.mrr * (gd.mrr_growth_rate_pct / 100)
        if net_new_mrr > 0:
            burn_multiple = gd.monthly_burn / (net_new_mrr * 12)
            if burn_multiple <= 1:
                score += 10
            elif burn_multiple <= 2:
                score += 8
            elif burn_multiple <= 3:
                score += 6
            elif burn_multiple <= 5:
                score += 3
            else:
                score += 1
            parts.append(f"Burn {burn_multiple:.1f}x")

    # 2b: Revenue per headcount (5 pts)
    if gd.monthly_revenue and gd.headcount and gd.headcount > 0:
        rev_per_head = gd.monthly_revenue / gd.headcount
        if rev_per_head >= 10_000_000:
            score += 5
        elif rev_per_head >= 5_000_000:
            score += 4
        elif rev_per_head >= 3_000_000:
            score += 3
        elif rev_per_head >= 1_000_000:
            score += 2
        else:
            score += 1

    # 2c: Customer count (5 pts)
    if gd.paying_customers is not None:
        if gd.paying_customers >= 50:
            score += 5
        elif gd.paying_customers >= 20:
            score += 4
        elif gd.paying_customers >= 10:
            score += 3
        elif gd.paying_customers >= 5:
            score += 2
        else:
            score += 1
        parts.append(f"{gd.paying_customers} customers")

    return {"value": min(score, 20), "max": 20, "label": ", ".join(parts) or "일부 데이터"}


# ---------------------------------------------------------------------------
# Factor 3: Funding Timing Urgency (20 pts)
# ---------------------------------------------------------------------------
def _compute_funding_urgency(gd) -> dict:
    if gd is None:
        return {"value": 0, "max": 20, "label": "데이터 없음"}

    score = 0
    parts = []

    # 3a: Runway urgency (12 pts)
    runway = gd.runway_months
    if runway is None and gd.cash_on_hand and gd.monthly_burn and gd.monthly_burn > 0:
        runway = gd.cash_on_hand / gd.monthly_burn

    if runway is not None:
        if 3 <= runway <= 6:
            score += 12
        elif 6 < runway <= 9:
            score += 10
        elif 9 < runway <= 12:
            score += 6
        elif runway > 12:
            score += 2
        elif 1 <= runway < 3:
            score += 8
        else:
            score += 1
        parts.append(f"Runway {runway:.0f}mo")

    # 3b: Time since last funding (8 pts)
    if gd.last_funding_date:
        now = datetime.now(timezone.utc)
        if gd.last_funding_date.tzinfo is None:
            funding_date = gd.last_funding_date.replace(tzinfo=timezone.utc)
        else:
            funding_date = gd.last_funding_date
        months_since = (now.year - funding_date.year) * 12 + (now.month - funding_date.month)
        if 12 <= months_since <= 18:
            score += 8
        elif 18 < months_since <= 24:
            score += 7
        elif 9 <= months_since < 12:
            score += 5
        elif months_since > 24:
            score += 4
        else:
            score += 2
        parts.append(f"{months_since}mo since funding")

    return {"value": min(score, 20), "max": 20, "label": ", ".join(parts) or "데이터 없음"}


# ---------------------------------------------------------------------------
# Factor 5: Comment Signals (10 pts)
# ---------------------------------------------------------------------------
def _compute_comment_score(comments: list) -> int:
    if not comments:
        return 5  # Neutral

    positive = ["투자", "만나", "좋", "인상", "매력", "성장", "성과", "재미",
                "관심", "가능성", "매출", "급성장", "확장", "고객"]
    negative = ["반대", "패스", "비싼", "비싸", "부족", "불가",
                "리스크", "우려", "약", "탈락", "하락", "감소", "손실"]

    pos = neg = 0
    for text in comments:
        for kw in positive:
            pos += text.count(kw)
        for kw in negative:
            neg += text.count(kw)

    total = pos + neg
    if total == 0:
        return 5
    ratio = pos / total
    return int(ratio * 10)


# ---------------------------------------------------------------------------
# Factor 6: Stage & Valuation Fit (10 pts)
# ---------------------------------------------------------------------------
def _compute_stage_valuation(company) -> dict:
    # Stage fit (5 pts)
    stage_scores = {"seed": 5, "pre-a": 4, "a": 3, "pre-seed": 2, "none": 1}
    stage_val = stage_scores.get(company.current_stage or "none", 1)

    # Valuation attractiveness (5 pts)
    val_score = 3  # neutral default
    if company.valuation_usd is not None:
        typical = {"pre-seed": (1, 5), "seed": (3, 15), "pre-a": (8, 30), "a": (15, 50), "none": (1, 10)}
        low, high = typical.get(company.current_stage or "none", (1, 50))
        if company.valuation_usd <= low:
            val_score = 5
        elif company.valuation_usd <= (low + high) / 2:
            val_score = 4
        elif company.valuation_usd <= high:
            val_score = 2
        else:
            val_score = 1

    total = stage_val + val_score
    return {"value": min(total, 10), "max": 10, "label": f"{company.current_stage or 'none'}, {company.current_valuation or 0} {company.current_currency}"}


# ---------------------------------------------------------------------------
# Data completeness (0-100%)
# ---------------------------------------------------------------------------
def _compute_data_completeness(gd) -> float:
    if gd is None:
        return 0.0
    fields = [
        gd.monthly_revenue,
        gd.mrr_growth_rate_pct,
        gd.monthly_burn,
        gd.runway_months or (gd.cash_on_hand and gd.monthly_burn),
        gd.last_funding_date,
        gd.headcount,
        gd.paying_customers,
        gd.ndr_pct,
    ]
    filled = sum(1 for f in fields if f is not None and f is not False and f != 0)
    return round(filled / len(fields) * 100, 1)
