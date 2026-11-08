from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ReportCreate(BaseModel):
    profile_url: HttpUrl
    profile_name: str | None = None
    reason_category: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=20, max_length=5000)
    evidence_urls: list[HttpUrl] = Field(default_factory=list, max_length=10)

class ReportOut(BaseModel):
    id: int
    profile_id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProfileOut(BaseModel):
    id: int
    platform: str
    profile_url: str
    current_name: str | None
    status: str
    model_config = ConfigDict(from_attributes=True)

class ProfileChangeOut(BaseModel):
    field_name: str
    old_value: str | None
    new_value: str | None
    observed_at: datetime
    source_note: str | None
    model_config = ConfigDict(from_attributes=True)
