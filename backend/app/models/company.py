from __future__ import annotations
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=False, index=True)
    representative_name = Column(String)
    current_valuation = Column(Float)
    current_currency = Column(String, default="KRW")
    valuation_usd = Column(Float)  # Normalized to USD millions
    current_stage = Column(String)  # pre-seed, seed, pre-a, a, none
    deal_status = Column(String)  # 최종탈락, 트래킹
    batch = Column(String)
    sector = Column(String, nullable=True)
    traffic_score = Column(String, default="red")  # green, yellow, red
    score_value = Column(Integer, default=0)  # 0-100 numeric score
    score_details = Column(Text, nullable=True)  # JSON

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Growth-focused fields
    has_growth_data = Column(Integer, default=0)
    growth_data_completeness = Column(Float, default=0.0)

    comments = relationship("InvestmentComment", back_populates="company", cascade="all, delete-orphan")
    metric_snapshots = relationship("CompanyMetricSnapshot", back_populates="company", cascade="all, delete-orphan")
    slack_channels = relationship("SlackChannelMapping", back_populates="company", cascade="all, delete-orphan")
    growth_metrics = relationship("GrowthMetrics", back_populates="company", cascade="all, delete-orphan", order_by="GrowthMetrics.metric_date.desc()")
    score_history = relationship("ScoreHistory", back_populates="company", cascade="all, delete-orphan", order_by="ScoreHistory.created_at.desc()")


class CompanyMetricSnapshot(Base):
    __tablename__ = "company_metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    valuation = Column(Float)
    currency = Column(String)
    stage = Column(String)
    status = Column(String)
    upload_id = Column(Integer, ForeignKey("upload_history.id"), nullable=True)
    snapshot_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="metric_snapshots")


class GrowthMetrics(Base):
    __tablename__ = "growth_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    metric_date = Column(DateTime, nullable=False)

    # Revenue metrics
    monthly_revenue = Column(Float, nullable=True)
    revenue_currency = Column(String, default="KRW")
    arr = Column(Float, nullable=True)
    mrr = Column(Float, nullable=True)
    revenue_at_first_meeting = Column(Float, nullable=True)
    mrr_growth_rate_pct = Column(Float, nullable=True)

    # Burn & runway
    monthly_burn = Column(Float, nullable=True)
    cash_on_hand = Column(Float, nullable=True)
    runway_months = Column(Float, nullable=True)

    # Team & customers
    headcount = Column(Integer, nullable=True)
    paying_customers = Column(Integer, nullable=True)
    ndr_pct = Column(Float, nullable=True)

    # Key metrics (flexible)
    key_metric_value = Column(Float, nullable=True)
    key_metric_name = Column(String, nullable=True)

    # Last funding info
    last_funding_date = Column(DateTime, nullable=True)
    last_funding_amount = Column(Float, nullable=True)
    last_funding_round = Column(String, nullable=True)

    # Investors
    investors = Column(Text, nullable=True)  # JSON: [{"name":"...","round":"...","role":"lead|follow"}]

    # Meta
    notes = Column(Text, nullable=True)
    upload_id = Column(Integer, ForeignKey("upload_history.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="growth_metrics")
