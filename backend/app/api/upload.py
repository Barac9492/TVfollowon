from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.company import Company, CompanyMetricSnapshot, GrowthMetrics
from app.models.comment import InvestmentComment
from app.models.upload import UploadHistory
from app.schemas.upload import UploadResponse, UploadHistoryItem
from app.services.excel_parser import parse_portfolio_excel, parse_comments_excel, parse_growth_excel
from app.services.scoring import compute_traffic_score
from app.utils.currency import normalize_to_usd

router = APIRouter(prefix="/upload", tags=["upload"])


def _rescore_all(db: Session):
    """Rescore all companies with growth-focused algorithm."""
    for company in db.query(Company).all():
        comments = db.query(InvestmentComment).filter(
            InvestmentComment.company_id == company.id
        ).all()
        # Get latest growth data
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


@router.post("/portfolio", response_model=UploadResponse)
async def upload_portfolio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename or "portfolio.xlsx")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    rows = parse_portfolio_excel(file_path)
    errors = []
    created = 0
    updated = 0

    upload = UploadHistory(
        filename=file.filename or "portfolio.xlsx",
        file_type="portfolio",
        rows_parsed=len(rows),
    )
    db.add(upload)
    db.flush()

    for row in rows:
        try:
            val_usd = normalize_to_usd(row.get("current_valuation"), row.get("current_currency", "KRW"))
            existing = db.query(Company).filter(Company.id == row["id"]).first()

            if existing:
                existing.company_name = row.get("company_name") or existing.company_name
                existing.representative_name = row.get("representative_name") or existing.representative_name
                existing.current_valuation = row.get("current_valuation")
                existing.current_currency = row.get("current_currency", "KRW")
                existing.valuation_usd = val_usd
                existing.current_stage = row.get("current_stage")
                existing.deal_status = row.get("status")
                existing.batch = row.get("batch")
                updated += 1
            else:
                company = Company(
                    id=row["id"],
                    company_name=row.get("company_name", "Unknown"),
                    representative_name=row.get("representative_name"),
                    current_valuation=row.get("current_valuation"),
                    current_currency=row.get("current_currency", "KRW"),
                    valuation_usd=val_usd,
                    current_stage=row.get("current_stage"),
                    deal_status=row.get("status"),
                    batch=row.get("batch"),
                )
                db.add(company)
                created += 1

            snapshot = CompanyMetricSnapshot(
                company_id=row["id"],
                valuation=row.get("current_valuation"),
                currency=row.get("current_currency", "KRW"),
                stage=row.get("current_stage"),
                status=row.get("status"),
                upload_id=upload.id,
            )
            db.add(snapshot)
        except Exception as e:
            errors.append(f"Row {row.get('id', '?')}: {str(e)}")

    upload.rows_created = created
    upload.rows_updated = updated
    upload.errors = json.dumps(errors, ensure_ascii=False) if errors else None

    _rescore_all(db)
    db.commit()

    return UploadResponse(
        upload_id=upload.id,
        filename=file.filename or "portfolio.xlsx",
        file_type="portfolio",
        rows_parsed=len(rows),
        rows_created=created,
        rows_updated=updated,
        errors=errors,
    )


@router.post("/comments", response_model=UploadResponse)
async def upload_comments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename or "comments.xlsx")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    rows = parse_comments_excel(file_path)
    errors = []
    created = 0

    upload = UploadHistory(
        filename=file.filename or "comments.xlsx",
        file_type="comments",
        rows_parsed=len(rows),
    )
    db.add(upload)
    db.flush()

    for row in rows:
        try:
            company_id = row.get("company_id")
            if not company_id:
                errors.append(f"Missing company_id for comment: {row.get('company_name', '?')}")
                continue

            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                errors.append(f"Company not found: {company_id} ({row.get('company_name', '?')})")
                continue

            comment = InvestmentComment(
                company_id=company_id,
                company_name=row.get("company_name"),
                comment_text=row.get("comment_text", ""),
            )
            db.add(comment)
            created += 1
        except Exception as e:
            errors.append(f"Comment error: {str(e)}")

    upload.rows_created = created
    upload.errors = json.dumps(errors, ensure_ascii=False) if errors else None

    _rescore_all(db)
    db.commit()

    return UploadResponse(
        upload_id=upload.id,
        filename=file.filename or "comments.xlsx",
        file_type="comments",
        rows_parsed=len(rows),
        rows_created=created,
        rows_updated=0,
        errors=errors,
    )


@router.post("/growth", response_model=UploadResponse)
async def upload_growth(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload growth metrics Excel file."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename or "growth.xlsx")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    rows = parse_growth_excel(file_path)
    errors = []
    created = 0

    upload = UploadHistory(
        filename=file.filename or "growth.xlsx",
        file_type="growth",
        rows_parsed=len(rows),
    )
    db.add(upload)
    db.flush()

    for row in rows:
        try:
            company_id = row.get("company_id")
            if not company_id:
                errors.append("Missing company_id")
                continue

            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                errors.append(f"Company not found: {company_id} ({row.get('company_name', '?')})")
                continue

            metric_date = row.get("metric_date") or datetime.now(timezone.utc)

            gm = GrowthMetrics(
                company_id=company_id,
                metric_date=metric_date,
                monthly_revenue=row.get("monthly_revenue"),
                revenue_currency=row.get("revenue_currency", "KRW"),
                arr=row.get("arr"),
                mrr=row.get("mrr"),
                revenue_at_first_meeting=row.get("revenue_at_first_meeting"),
                mrr_growth_rate_pct=row.get("mrr_growth_rate_pct"),
                monthly_burn=row.get("monthly_burn"),
                cash_on_hand=row.get("cash_on_hand"),
                runway_months=row.get("runway_months"),
                headcount=row.get("headcount"),
                key_metric_value=row.get("key_metric_value"),
                key_metric_name=row.get("key_metric_name"),
                last_funding_date=row.get("last_funding_date"),
                last_funding_amount=row.get("last_funding_amount"),
                last_funding_round=row.get("last_funding_round"),
                paying_customers=row.get("paying_customers"),
                ndr_pct=row.get("ndr_pct"),
                notes=row.get("notes"),
                upload_id=upload.id,
            )
            db.add(gm)
            created += 1
        except Exception as e:
            errors.append(f"Growth row {row.get('company_id', '?')}: {str(e)}")

    upload.rows_created = created
    upload.errors = json.dumps(errors, ensure_ascii=False) if errors else None

    db.flush()
    _rescore_all(db)
    db.commit()

    return UploadResponse(
        upload_id=upload.id,
        filename=file.filename or "growth.xlsx",
        file_type="growth",
        rows_parsed=len(rows),
        rows_created=created,
        rows_updated=0,
        errors=errors,
    )


@router.get("/growth-template")
def download_growth_template():
    """Download blank growth metrics template."""
    from app.services.template_generator import generate_growth_template
    data = generate_growth_template()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=growth_template.xlsx"},
    )


@router.get("/growth-template-prefilled")
def download_growth_template_prefilled(db: Session = Depends(get_db)):
    """Download growth template pre-filled with company IDs."""
    from app.services.template_generator import generate_growth_template
    companies = db.query(Company.id, Company.company_name).order_by(Company.company_name).all()
    data = generate_growth_template(companies=[(c.id, c.company_name) for c in companies])
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=growth_template_prefilled.xlsx"},
    )


@router.get("/history", response_model=list[UploadHistoryItem])
def get_upload_history(db: Session = Depends(get_db)):
    uploads = db.query(UploadHistory).order_by(UploadHistory.uploaded_at.desc()).all()
    return uploads
