from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.company import Company, GrowthMetrics
from app.models.comment import InvestmentComment
from app.schemas.company import (
    CompanyListItem,
    CompanyListResponse,
    CompanyDetail,
    CommentItem,
    MetricSnapshotItem,
    GrowthMetricsItem,
    DashboardStats,
    ActionItem,
)
from app.services.action_items import generate_action_items, get_top_action_items

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(
    search: str = Query(None),
    stage: str = Query(None),
    score: str = Query(None),
    status: str = Query(None),
    has_growth_data: int = Query(None),
    sort_by: str = Query("score_value"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Company)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Company.company_name.ilike(search_term))
            | (Company.representative_name.ilike(search_term))
        )
    if stage:
        query = query.filter(Company.current_stage == stage)
    if score:
        query = query.filter(Company.traffic_score == score)
    if status:
        query = query.filter(Company.deal_status == status)
    if has_growth_data is not None:
        query = query.filter(Company.has_growth_data == has_growth_data)

    total = query.count()

    sort_column = getattr(Company, sort_by, Company.score_value)
    if sort_dir == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    companies = query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for c in companies:
        comment_count = db.query(func.count(InvestmentComment.id)).filter(
            InvestmentComment.company_id == c.id
        ).scalar() or 0

        # Get latest growth snapshot for card display
        latest_gm = db.query(GrowthMetrics).filter(
            GrowthMetrics.company_id == c.id
        ).order_by(GrowthMetrics.metric_date.desc()).first()

        all_actions = generate_action_items(c.score_details, latest_gm, comment_count)
        top_actions = get_top_action_items(all_actions, 2)

        item = CompanyListItem(
            id=c.id,
            company_name=c.company_name,
            representative_name=c.representative_name,
            current_valuation=c.current_valuation,
            current_currency=c.current_currency,
            valuation_usd=c.valuation_usd,
            current_stage=c.current_stage,
            deal_status=c.deal_status,
            batch=c.batch,
            sector=c.sector,
            traffic_score=c.traffic_score,
            score_value=c.score_value,
            comment_count=comment_count,
            has_growth_data=c.has_growth_data or 0,
            growth_data_completeness=c.growth_data_completeness or 0.0,
            mrr_growth_rate_pct=latest_gm.mrr_growth_rate_pct if latest_gm else None,
            runway_months=latest_gm.runway_months if latest_gm else None,
            monthly_revenue=latest_gm.monthly_revenue if latest_gm else None,
            investors=latest_gm.investors if latest_gm else None,
            top_action_items=[ActionItem(**a) for a in top_actions],
        )
        items.append(item)

    return CompanyListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Company.id)).scalar() or 0
    green = db.query(func.count(Company.id)).filter(Company.traffic_score == "green").scalar() or 0
    yellow = db.query(func.count(Company.id)).filter(Company.traffic_score == "yellow").scalar() or 0
    red = db.query(func.count(Company.id)).filter(Company.traffic_score == "red").scalar() or 0

    stage_counts = db.query(Company.current_stage, func.count(Company.id)).group_by(Company.current_stage).all()
    by_stage = {s or "none": c for s, c in stage_counts}

    status_counts = db.query(Company.deal_status, func.count(Company.id)).group_by(Company.deal_status).all()
    by_status = {s or "unknown": c for s, c in status_counts}

    avg_val = db.query(func.avg(Company.valuation_usd)).filter(Company.valuation_usd.isnot(None)).scalar()

    # Growth stats
    growth_count = db.query(func.count(Company.id)).filter(Company.has_growth_data == 1).scalar() or 0
    avg_mrr = db.query(func.avg(GrowthMetrics.mrr_growth_rate_pct)).filter(
        GrowthMetrics.mrr_growth_rate_pct.isnot(None)
    ).scalar()

    # Companies in funding window (runway 3-9 months)
    funding_window = db.query(func.count(GrowthMetrics.id.distinct())).filter(
        GrowthMetrics.runway_months.isnot(None),
        GrowthMetrics.runway_months >= 3,
        GrowthMetrics.runway_months <= 9,
    ).scalar() or 0

    return DashboardStats(
        total_companies=total,
        green_count=green,
        yellow_count=yellow,
        red_count=red,
        by_stage=by_stage,
        by_status=by_status,
        avg_valuation_usd=round(avg_val, 2) if avg_val else None,
        growth_data_count=growth_count,
        avg_mrr_growth=round(avg_mrr, 1) if avg_mrr else None,
        funding_window_count=funding_window,
    )


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company_detail(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    comments = db.query(InvestmentComment).filter(
        InvestmentComment.company_id == company_id
    ).order_by(InvestmentComment.created_at.desc()).all()

    snapshots = company.metric_snapshots

    growth_metrics = db.query(GrowthMetrics).filter(
        GrowthMetrics.company_id == company_id
    ).order_by(GrowthMetrics.metric_date.desc()).all()

    latest_gm = growth_metrics[0] if growth_metrics else None

    all_actions = generate_action_items(company.score_details, latest_gm, len(comments))
    top_actions = get_top_action_items(all_actions, 2)

    return CompanyDetail(
        id=company.id,
        company_name=company.company_name,
        representative_name=company.representative_name,
        current_valuation=company.current_valuation,
        current_currency=company.current_currency,
        valuation_usd=company.valuation_usd,
        current_stage=company.current_stage,
        deal_status=company.deal_status,
        batch=company.batch,
        sector=company.sector,
        traffic_score=company.traffic_score,
        score_value=company.score_value,
        score_details=company.score_details,
        created_at=company.created_at,
        updated_at=company.updated_at,
        comment_count=len(comments),
        has_growth_data=company.has_growth_data or 0,
        growth_data_completeness=company.growth_data_completeness or 0.0,
        mrr_growth_rate_pct=latest_gm.mrr_growth_rate_pct if latest_gm else None,
        runway_months=latest_gm.runway_months if latest_gm else None,
        monthly_revenue=latest_gm.monthly_revenue if latest_gm else None,
        investors=latest_gm.investors if latest_gm else None,
        comments=[CommentItem.model_validate(c) for c in comments],
        metric_snapshots=[MetricSnapshotItem.model_validate(s) for s in snapshots],
        growth_metrics=[GrowthMetricsItem.model_validate(g) for g in growth_metrics],
        top_action_items=[ActionItem(**a) for a in top_actions],
        action_items=[ActionItem(**a) for a in all_actions],
    )
