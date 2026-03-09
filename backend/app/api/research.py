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
    ChatRequest,
    ChatResponse,
    AutoResearchResult,
)
from app.services.research_service import research_service
from app.services.scoring import compute_traffic_score
from app.services.score_tracker import record_score_change

router = APIRouter(prefix="/research", tags=["research"])


def _rescore_company(
    company: Company,
    db: Session,
    trigger_type: str = "unknown",
    trigger_detail: str = "",
):
    """Rescore a single company after data change and record history."""
    comments = db.query(InvestmentComment).filter(
        InvestmentComment.company_id == company.id
    ).all()
    latest_growth = db.query(GrowthMetrics).filter(
        GrowthMetrics.company_id == company.id
    ).order_by(GrowthMetrics.metric_date.desc()).first()

    color, value, details = compute_traffic_score(company, comments, latest_growth)

    # Record score history BEFORE updating company (so we capture old values)
    record_score_change(
        company=company,
        new_color=color,
        new_value=value,
        new_details_json=details,
        trigger_type=trigger_type,
        trigger_detail=trigger_detail,
        db=db,
    )

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

    _rescore_company(company, db, trigger_type="research_approve", trigger_detail=f"연구 #{log.id} 승인")
    db.commit()

    return ApproveResponse(
        growth_metrics_id=gm.id,
        company_id=log.company_id,
        message="성장 데이터가 저장되었습니다.",
    )


def _save_metrics_from_research(metrics: dict, company_id: str, db: Session) -> int | None:
    """Save metrics from research result. Returns growth_metrics_id or None if no meaningful data."""
    # Check if any meaningful data was found
    data_fields = [
        "monthly_revenue", "mrr", "arr", "mrr_growth_rate_pct",
        "monthly_burn", "cash_on_hand", "runway_months",
        "headcount", "paying_customers", "last_funding_round",
        "last_funding_amount",
    ]
    has_data = any(metrics.get(f) is not None for f in data_fields)
    has_investors = bool(metrics.get("investors") and len(metrics["investors"]) > 0)

    if not has_data and not has_investors:
        return None

    # Convert investors
    investors_json = None
    investors_data = metrics.get("investors")
    if investors_data:
        if isinstance(investors_data, list):
            investors_json = json.dumps(investors_data, ensure_ascii=False)
        elif isinstance(investors_data, str):
            investors_json = investors_data

    # Parse funding date
    funding_date = None
    if metrics.get("last_funding_date"):
        try:
            funding_date = datetime.strptime(str(metrics["last_funding_date"]), "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    gm = GrowthMetrics(
        company_id=company_id,
        metric_date=datetime.now(timezone.utc),
        monthly_revenue=metrics.get("monthly_revenue"),
        revenue_currency=metrics.get("revenue_currency", "KRW"),
        arr=metrics.get("arr"),
        mrr=metrics.get("mrr"),
        mrr_growth_rate_pct=metrics.get("mrr_growth_rate_pct"),
        monthly_burn=metrics.get("monthly_burn"),
        cash_on_hand=metrics.get("cash_on_hand"),
        runway_months=metrics.get("runway_months"),
        headcount=int(metrics["headcount"]) if metrics.get("headcount") is not None else None,
        paying_customers=int(metrics["paying_customers"]) if metrics.get("paying_customers") is not None else None,
        ndr_pct=metrics.get("ndr_pct"),
        key_metric_value=metrics.get("key_metric_value"),
        key_metric_name=metrics.get("key_metric_name"),
        last_funding_date=funding_date,
        last_funding_amount=metrics.get("last_funding_amount"),
        last_funding_round=metrics.get("last_funding_round"),
        investors=investors_json,
        notes=metrics.get("notes"),
    )
    db.add(gm)
    db.flush()
    return gm.id


@router.post("/auto-research/{company_id}", response_model=AutoResearchResult)
def auto_research_company(company_id: str, db: Session = Depends(get_db)):
    """Run web research on a company and auto-save results."""
    if not research_service.enabled:
        raise HTTPException(status_code=400, detail="AI 서비스가 비활성화되어 있습니다.")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return AutoResearchResult(
            company_id=company_id, company_name="Unknown",
            success=False, error="회사를 찾을 수 없습니다.",
        )

    try:
        result = research_service.web_research(company.company_name)
    except ValueError as e:
        return AutoResearchResult(
            company_id=company_id, company_name=company.company_name,
            success=False, error=str(e),
        )

    metrics = result["metrics"]
    confidence = _compute_confidence(metrics)

    # Log the research
    log = ResearchLog(
        company_id=company_id,
        research_type="web_research",
        raw_result=result["raw"],
        extracted_metrics=json.dumps(metrics, ensure_ascii=False),
        status="pending",
    )
    db.add(log)
    db.flush()

    # Auto-save if meaningful data was found
    gm_id = _save_metrics_from_research(metrics, company_id, db)
    has_data = gm_id is not None

    if has_data:
        log.status = "approved"
        log.growth_metrics_id = gm_id
        _rescore_company(company, db, trigger_type="auto_research", trigger_detail=f"웹 리서치: {company.company_name}")
    else:
        log.status = "approved"  # Mark as complete even if no data

    db.commit()

    return AutoResearchResult(
        company_id=company_id,
        company_name=company.company_name,
        success=True,
        has_data=has_data,
        confidence=confidence,
        notes=metrics.get("notes"),
    )


@router.delete("/clear-growth-data")
def clear_all_growth_data(db: Session = Depends(get_db)):
    """Clear all growth metrics data (use to remove sample data)."""
    count = db.query(GrowthMetrics).count()
    db.query(GrowthMetrics).delete()
    db.query(ResearchLog).delete()

    # Reset company growth flags and rescore
    for company in db.query(Company).all():
        company.has_growth_data = 0
        company.growth_data_completeness = 0.0
        _rescore_company(company, db, trigger_type="data_clear", trigger_detail="성장 데이터 전체 삭제")

    db.commit()
    return {"deleted": count, "message": f"{count}건의 성장 데이터가 삭제되었습니다."}


@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(data: ChatRequest, db: Session = Depends(get_db)):
    """Multi-turn conversation about a company's growth and data triangulation."""
    if not research_service.enabled:
        raise HTTPException(status_code=400, detail="AI 서비스가 비활성화되어 있습니다.")

    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")

    # Build company context from database
    latest_gm = db.query(GrowthMetrics).filter(
        GrowthMetrics.company_id == company.id
    ).order_by(GrowthMetrics.metric_date.desc()).first()

    comments = db.query(InvestmentComment).filter(
        InvestmentComment.company_id == company.id
    ).order_by(InvestmentComment.created_at.desc()).limit(5).all()

    context_parts = [
        f"Company: {company.company_name}",
        f"Representative: {company.representative_name or 'Unknown'}",
        f"Stage: {company.current_stage or 'Unknown'}",
        f"Deal Status: {company.deal_status or 'Unknown'}",
        f"Valuation: {company.current_valuation or 'Unknown'} {company.current_currency or 'KRW'}",
        f"Traffic Score: {company.traffic_score or 'Unknown'} (value: {company.score_value or 0})",
    ]

    if latest_gm:
        gm_parts = []
        if latest_gm.monthly_revenue:
            gm_parts.append(f"Monthly Revenue: {latest_gm.monthly_revenue}")
        if latest_gm.mrr:
            gm_parts.append(f"MRR: {latest_gm.mrr}")
        if latest_gm.arr:
            gm_parts.append(f"ARR: {latest_gm.arr}")
        if latest_gm.mrr_growth_rate_pct is not None:
            gm_parts.append(f"MRR Growth: {latest_gm.mrr_growth_rate_pct}%")
        if latest_gm.monthly_burn:
            gm_parts.append(f"Monthly Burn: {latest_gm.monthly_burn}")
        if latest_gm.runway_months is not None:
            gm_parts.append(f"Runway: {latest_gm.runway_months} months")
        if latest_gm.headcount is not None:
            gm_parts.append(f"Headcount: {latest_gm.headcount}")
        if latest_gm.paying_customers is not None:
            gm_parts.append(f"Paying Customers: {latest_gm.paying_customers}")
        if latest_gm.last_funding_round:
            gm_parts.append(f"Last Funding: {latest_gm.last_funding_round}")
        if latest_gm.investors:
            gm_parts.append(f"Investors: {latest_gm.investors}")
        if gm_parts:
            context_parts.append(f"\nGrowth Data (latest):\n" + "\n".join(gm_parts))
    else:
        context_parts.append("\nNo growth data available yet.")

    if comments:
        comment_texts = [f"- {c.comment_text[:200]}" for c in comments[:5]]
        context_parts.append(f"\nRecent Comments:\n" + "\n".join(comment_texts))

    company_context = "\n".join(context_parts)

    # Convert history to list of dicts
    history = [{"role": m.role, "content": m.content} for m in data.history]

    try:
        reply = research_service.chat(data.message, company_context, history)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return ChatResponse(reply=reply)


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


@router.get("/debug-search/{company_id}")
def debug_search(company_id: str, db: Session = Depends(get_db)):
    """Debug endpoint: raw API call to diagnose web search block structure."""
    if not research_service.enabled:
        return {"error": "AI 서비스 비활성화"}

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return {"error": "회사 없음"}

    try:
        import anthropic
        sdk_version = anthropic.__version__
    except Exception:
        sdk_version = "unknown"

    try:
        # Make a raw API call to inspect every response block
        client = research_service.client
        name = company.company_name
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=("한국 스타트업 투자 유치 정보를 검색하여 JSON으로 반환하세요. "
                    "investors 배열에 투자자 이름, 라운드, 역할을 포함하세요."),
            messages=[{
                "role": "user",
                "content": f"'{name} 투자 유치' 검색 후 투자자, 금액, 라운드를 JSON으로 반환하세요.",
            }],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
                "user_location": {
                    "type": "approximate",
                    "country": "KR",
                    "timezone": "Asia/Seoul",
                },
            }],
        )

        # Inspect every block in the response
        blocks_info = []
        for i, block in enumerate(response.content):
            block_type = getattr(block, "type", "unknown")
            info = {"index": i, "type": block_type}
            if hasattr(block, "text"):
                info["text_length"] = len(block.text)
                info["text_preview"] = block.text[:400]
            if hasattr(block, "name"):
                info["tool_name"] = block.name
            if hasattr(block, "content") and block_type == "web_search_tool_result":
                search_results = getattr(block, "content", [])
                info["search_result_count"] = len(search_results) if isinstance(search_results, list) else "N/A"
            blocks_info.append(info)

        # Also run through the full web_research pipeline
        result = research_service.web_research(name)
        metrics = result["metrics"]

        return {
            "company_name": name,
            "sdk_version": sdk_version,
            "stop_reason": response.stop_reason,
            "total_blocks": len(response.content),
            "blocks": blocks_info,
            "pipeline_raw_length": len(result.get("raw", "")),
            "pipeline_raw_preview": result.get("raw", "")[:500],
            "investors_found": metrics.get("investors", []),
            "notes": metrics.get("notes", ""),
            "sources": metrics.get("sources", []),
            "all_non_null_fields": {
                k: v for k, v in metrics.items()
                if v is not None and v != [] and v != ""
            },
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc(), "sdk_version": sdk_version}
