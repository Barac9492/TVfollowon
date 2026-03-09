from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class SlackStatus(BaseModel):
    connected: bool
    workspace_name: Optional[str] = None
    message: Optional[str] = None


class SlackChannelMap(BaseModel):
    company_id: str
    channel_id: str
    channel_name: Optional[str] = None


class SlackMessageItem(BaseModel):
    user_name: Optional[str] = None
    text: Optional[str] = None
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SlackSummaryItem(BaseModel):
    summary_text: str
    message_count: Optional[int] = None
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
