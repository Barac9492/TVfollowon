from __future__ import annotations
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company, GrowthMetrics
from app.models.comment import InvestmentComment
from app.models.research import ResearchLog
from app.schemas.research import (
    ResearchStatus,
    ExtractRequest,
    WebResearchRequest,
    ResearchResult,
    ApproveRequest,
    ApproveResponse,
    ResearchLogItem,
)
from app.services.research_service import research_service
from app.services.scoring import compute_traffic_score

router = APIRouter(prefix="/research", tags=["research"])


def _rescore_company(company: Company, db: Session):
    """Rescore a single company after data change."""
    comments = db.query(InvestmentComment).filter(
        InvestmentComment.company_id == company.id
    ).all()
    latest_growth = db.query(GrowthMetrics).filter(
        GrowthMetrics.company_id == company.id
    ).order_by(GrowthMetrics.metric_date.desc()).first()

    color, value, details = compute_traffic_score(company, comments, latest_growth)
    company.traffic_score = color
    company.score_value = value
    company.score_details = details
    company.has_growth_data = 1 if latest_growth else 0

    details_dict = json.loads(details)
    company.growth_data_completeness = details_dict.get("data_completeness", 0.0)


def _compute_confidence(metrics: dict) -> str:
    """Compute confidence level based on how many fields were extracted."""
    fields = [
        "monthly_revenue", "mrr", "arr", "mrr_growth_rate_pct",
        "monthly_burn", "cash_on_hand", "runway_months",
        "headcount", "paying_customers", "last_funding_round",
    ]
    filled = sum(1 for f in fields if metrics.get(f) is not None)
    if filled >= 7:
        return "high"
    elif filled >= 4:
        return "medium"
    return "low"


@router.get("/status", response_model=ResearchStatus)
def get_research_status():
    return ResearchStatus(
        enabled=research_service.enabled,
        message="AI 리서치 기능이 활성화되어 있습니다." if research_service.enabled
        else "CLAUDE_API_KEY가 설정되어 있지 않습니다. Settings에서 설정하세요.",
    )


@router.post("/extract", response_model=ResearchResult)
def extract_metrics(data: ExtractRequest, db: Session = Depends(get_db)):
    if not research_service.enabled:
        raise HTTPException(status_code=400, detail="AI 서비스가 비활성화되어 있습니다.")

    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    try:
        result = research_service.extract_from_text(data.text, data.company_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    metrics = result["metrics"]

    log = ResearchLog(
        company_id=data.company_id,
        research_type="text_extraction",
        input_text=data.text[:10000],  # Limit stored text
        raw_result=result["raw"],
        extracted_metrics=json.dumps(metrics, ensure_ascii=False),
        status="pending",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return ResearchResult(
        research_id=log.id,
        metrics=metrics,
        notes=metrics.get("notes"),
        sources=metrics.get("sources", []),
        confidence=_compute_confidence(metrics),
    )


@router.post("/web-search", response_model=ResearchResult)
def web_research(data: WebResearchRequest, db: Session = Depends(get_db)):
    if not research_service.enabled:
        raise HTTPException(status_code=400, detail="AI 서비스가 비활성화되어 있습니다.")

    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    try:
        result = research_service.web_research(data.company_name, data.additional_context)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    metrics = result["metrics"]

    log = ResearchLog(
        company_id=data.company_id,
        research_type="web_research",
        input_text=data.additional_context[:5000] if data.additional_context else None,
        raw_result=result["raw"],
        extracted_metrics=json.dumps(metrics, ensure_ascii=False),
        status="pending",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return ResearchResult(
        research_id=log.id,
        metrics=metrics,
        notes=metrics.get("notes"),
        sources=metrics.get("sources", []),
        confidence=_compute_confidence(metrics),
    )


@router.post("/approve/{research_id}", response_model=ApproveResponse)
def approve_research(
    research_id: int,
    data: ApproveRequest,
    db: Session = Depends(get_db),
):
    log = db.query(ResearchLog).filter(ResearchLog.id == research_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="리서치 기록을 찾을 수 없습니다.")
    if log.status == "approved":
        raise HTTPException(status_code=400, detail="이미 승인된 리서치입니다.")

    company = db.query(Company).filter(Company.id == log.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    m = data.metrics

    # Convert investors list to JSON string if present
    investors_json = None
    investors_data = m.get("investors")
    if investors_data:
        if isinstance(investors_data, list):
            investors_json = json.dumps(investors_data, ensure_ascii=False)
        elif isinstance(investors_data, str):
            investors_json = investors_data

    # Parse funding date
    funding_date = None
    if m.get("last_funding_date"):
        try:
            funding_date = datetime.strptime(str(m["last_funding_date"]), "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    gm = GrowthMetrics(
        company_id=log.company_id,
        metric_date=datetime.now(timezone.utc),
        monthly_revenue=m.get("monthly_revenue"),
        revenue_currency=m.get("revenue_currency", "KRW"),
        arr=m.get("arr"),
        mrr=m.get("mrr"),
        mrr_growth_rate_pct=m.get("mrr_growth_rate_pct"),
        monthly_burn=m.get("monthly_burn"),
        cash_on_hand=m.get("cash_on_hand"),
        runway_months=m.get("runway_months"),
        headcount=int(m["headcount"]) if m.get("headcount") is not None else None,
        paying_customers=int(m["paying_customers"]) if m.get("paying_customers") is not None else None,
        ndr_pct=m.get("ndr_pct"),
        key_metric_value=m.get("key_metric_value"),
        key_metric_name=m.get("key_metric_name"),
        last_funding_date=funding_date,
        last_funding_amount=m.get("last_funding_amount"),
        last_funding_round=m.get("last_funding_round"),
        investors=investors_json,
        notes=m.get("notes"),
    )
    db.add(gm)
    db.flush()

    log.status = "approved"
    log.growth_metrics_id = gm.id
    log.extracted_metrics = json.dumps(data.metrics, ensure_ascii=False)

    _rescore_company(company, db)
    db.commit()

    return ApproveResponse(
        growth_metrics_id=gm.id,
        company_id=log.company_id,
        message="성장 데이터가 저장되었습니다.",
    )


@router.get("/history/{company_id}", response_model=list[ResearchLogItem])
def get_research_history(company_id: str, db: Session = Depends(get_db)):
    logs = (
        db.query(ResearchLog)
        .filter(ResearchLog.company_id == company_id)
        .order_by(ResearchLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [ResearchLogItem.model_validate(log) for log in logs]
