from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ResearchStatus(BaseModel):
    enabled: bool
    message: str


class ExtractRequest(BaseModel):
    company_id: str
    text: str
    company_name: str


class WebResearchRequest(BaseModel):
    company_id: str
    company_name: str
    additional_context: str = ""


class ResearchResult(BaseModel):
    research_id: int
    metrics: Dict[str, Any]
    notes: Optional[str] = None
    sources: List[Dict[str, str]] = []
    confidence: str = "medium"


class ApproveRequest(BaseModel):
    metrics: Dict[str, Any]


class ApproveResponse(BaseModel):
    growth_metrics_id: int
    company_id: str
    message: str


class ResearchLogItem(BaseModel):
    id: int
    company_id: str
    research_type: str
    status: str
    extracted_metrics: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    company_id: str
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


class AutoResearchResult(BaseModel):
    company_id: str
    company_name: str
    success: bool
    has_data: bool = False
    confidence: str = "low"
    notes: Optional[str] = None
    error: Optional[str] = None


class BulkResearchResponse(BaseModel):
    total: int
    completed: int
    with_data: int
    results: List[AutoResearchResult]
