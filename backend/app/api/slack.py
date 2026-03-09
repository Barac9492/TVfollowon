from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.company import Company
from app.models.slack import SlackChannelMapping, SlackMessage, SlackSummary
from app.schemas.slack import SlackStatus, SlackChannelMap, SlackMessageItem, SlackSummaryItem
from app.services.slack_service import slack_service
from app.services.ai_summarizer import ai_summarizer

router = APIRouter(prefix="/slack", tags=["slack"])


@router.get("/status", response_model=SlackStatus)
def get_slack_status():
    status = slack_service.get_status()
    return SlackStatus(**status)


@router.get("/channels/search")
def search_channels(q: str = Query(""), db: Session = Depends(get_db)):
    if not slack_service.is_connected:
        return {"channels": [], "message": "Slack not connected"}
    channels = slack_service.search_channels(q)
    return {"channels": channels}


@router.post("/channels/map")
def map_channel(data: SlackChannelMap, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    mapping = SlackChannelMapping(
        company_id=data.company_id,
        slack_channel_id=data.channel_id,
        slack_channel_name=data.channel_name,
    )
    db.add(mapping)
    db.commit()
    return {"status": "ok", "mapping_id": mapping.id}


@router.post("/sync/{company_id}")
def sync_company_slack(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    mapping = db.query(SlackChannelMapping).filter(
        SlackChannelMapping.company_id == company_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="No Slack channel mapped for this company")

    # Fetch messages
    messages_data = slack_service.fetch_messages(mapping.slack_channel_id)

    for m in messages_data:
        existing = db.query(SlackMessage).filter(
            SlackMessage.channel_id == mapping.slack_channel_id,
            SlackMessage.message_ts == m["message_ts"],
        ).first()
        if not existing:
            db.add(SlackMessage(
                channel_id=mapping.slack_channel_id,
                message_ts=m["message_ts"],
                user_name=m["user_name"],
                text=m["text"],
                posted_at=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            ))

    # Generate AI summary
    all_messages = db.query(SlackMessage).filter(
        SlackMessage.channel_id == mapping.slack_channel_id
    ).order_by(SlackMessage.posted_at.desc()).limit(50).all()

    if all_messages:
        texts = [m.text for m in all_messages if m.text]
        summary_text = ai_summarizer.summarize_messages(texts, company.company_name)

        summary = SlackSummary(
            channel_id=mapping.slack_channel_id,
            summary_text=summary_text,
            message_count=len(all_messages),
            period_start=all_messages[-1].posted_at if all_messages else None,
            period_end=all_messages[0].posted_at if all_messages else None,
        )
        db.add(summary)

    db.commit()
    return {"messages_fetched": len(messages_data), "total_stored": len(all_messages) if all_messages else 0}


@router.get("/messages/{company_id}", response_model=list[SlackMessageItem])
def get_company_messages(company_id: str, db: Session = Depends(get_db)):
    mapping = db.query(SlackChannelMapping).filter(
        SlackChannelMapping.company_id == company_id
    ).first()
    if not mapping:
        return []

    messages = db.query(SlackMessage).filter(
        SlackMessage.channel_id == mapping.slack_channel_id
    ).order_by(SlackMessage.posted_at.desc()).limit(20).all()

    return [SlackMessageItem.model_validate(m) for m in messages]


@router.get("/summary/{company_id}")
def get_company_summary(company_id: str, db: Session = Depends(get_db)):
    mapping = db.query(SlackChannelMapping).filter(
        SlackChannelMapping.company_id == company_id
    ).first()
    if not mapping:
        return None

    summary = db.query(SlackSummary).filter(
        SlackSummary.channel_id == mapping.slack_channel_id
    ).order_by(SlackSummary.generated_at.desc()).first()

    if not summary:
        return None
    return SlackSummaryItem.model_validate(summary)
