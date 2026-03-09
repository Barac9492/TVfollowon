from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class UploadResponse(BaseModel):
    upload_id: int
    filename: str
    file_type: str
    rows_parsed: int
    rows_created: int
    rows_updated: int
    errors: List[str] = []


class UploadHistoryItem(BaseModel):
    id: int
    filename: str
    file_type: Optional[str] = None
    rows_parsed: int
    rows_created: int
    rows_updated: int
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
