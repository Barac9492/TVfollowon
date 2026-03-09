from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class ActionItem(BaseModel):
    type: str           # "missing_data" | "low_score" | "opportunity"
    field: str          # field name or factor name
    potential_points: int
    label: str          # Korean user-facing label
    detail: str = ""    # Additional context
    priority: str       # "high" | "medium" | "low"
    factor: str         # which scoring factor


class CompanyListItem(BaseModel):
    id: str
    company_name: str
    representative_name: Optional[str] = None
    current_valuation: Optional[float] = None
    current_currency: str = "KRW"
    valuation_usd: Optional[float] = None
    current_stage: Optional[str] = None
    deal_status: Optional[str] = None
    batch: Optional[str] = None
    sector: Optional[str] = None
    traffic_score: str = "red"
    score_value: int = 0
    comment_count: int = 0
    has_growth_data: int = 0
    growth_data_completeness: float = 0.0
    # Latest growth snapshot summary (for card display)
    mrr_growth_rate_pct: Optional[float] = None
    runway_months: Optional[float] = None
    monthly_revenue: Optional[float] = None
    # Investors (latest snapshot)
    investors: Optional[str] = None
    # Actionable insights (top 1-2 items for card)
    top_action_items: List[ActionItem] = []

    class Config:
        from_attributes = True


class GrowthMetricsItem(BaseModel):
    id: int
    metric_date: Optional[datetime] = None
    monthly_revenue: Optional[float] = None
    revenue_currency: Optional[str] = "KRW"
    arr: Optional[float] = None
    mrr: Optional[float] = None
    revenue_at_first_meeting: Optional[float] = None
    mrr_growth_rate_pct: Optional[float] = None
    monthly_burn: Optional[float] = None
    cash_on_hand: Optional[float] = None
    runway_months: Optional[float] = None
    headcount: Optional[int] = None
    paying_customers: Optional[int] = None
    ndr_pct: Optional[float] = None
    key_metric_value: Optional[float] = None
    key_metric_name: Optional[str] = None
    last_funding_date: Optional[datetime] = None
    last_funding_amount: Optional[float] = None
    last_funding_round: Optional[str] = None
    investors: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ScoreHistoryItem(BaseModel):
    id: int
    score_value: int
    traffic_score: str
    score_details: Optional[str] = None
    previous_score_value: Optional[int] = None
    previous_traffic_score: Optional[str] = None
    score_change: int = 0
    change_reasons: Optional[str] = None  # JSON string
    meta_insight: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_detail: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyDetail(CompanyListItem):
    score_details: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comments: List["CommentItem"] = []
    metric_snapshots: List["MetricSnapshotItem"] = []
    growth_metrics: List["GrowthMetricsItem"] = []
    score_history: List["ScoreHistoryItem"] = []
    # Full actionable insights list
    action_items: List[ActionItem] = []


class CommentItem(BaseModel):
    id: int
    comment_text: str
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetricSnapshotItem(BaseModel):
    id: int
    valuation: Optional[float] = None
    currency: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    snapshot_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    items: List[CompanyListItem]
    total: int
    page: int
    per_page: int


class DashboardStats(BaseModel):
    total_companies: int
    green_count: int
    yellow_count: int
    red_count: int
    by_stage: Dict[str, int]
    by_status: Dict[str, int]
    avg_valuation_usd: Optional[float] = None
    growth_data_count: int = 0
    avg_mrr_growth: Optional[float] = None
    funding_window_count: int = 0
