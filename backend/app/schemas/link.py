from pydantic import BaseModel, AnyHttpUrl
from typing import Optional
from datetime import datetime

class LinkBase(BaseModel):
    original_url: AnyHttpUrl

class LinkCreate(LinkBase):
    custom_alias: Optional[str] = None
    expires_in_days: Optional[int] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: Optional[AnyHttpUrl] = None
    expires_in_days: Optional[int] = None
    expires_at: Optional[datetime] = None

class LinkOut(LinkBase):
    id: int
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int

    class Config:
        orm_mode = True

class LinkStats(BaseModel):
    original_url: AnyHttpUrl
    created_at: datetime
    access_count: int
    last_accessed: Optional[datetime] = None

class LinkSearchOut(BaseModel):
    short_code: str
    original_url: AnyHttpUrl