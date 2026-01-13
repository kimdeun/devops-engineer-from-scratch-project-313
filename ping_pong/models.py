import os
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


def get_base_url() -> str:
    """Получает базовый URL из переменной окружения"""
    return os.getenv("BASE_URL", "https://short.io")


# SQLModel for Link
class Link(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    original_url: str
    short_name: str = Field(unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def short_url(self) -> str:
        base_url = get_base_url()
        return f"{base_url}/r/{self.short_name}"


# Pydantic models for request/response
class LinkCreate(SQLModel):
    original_url: str
    short_name: str


class LinkResponse(SQLModel):
    id: int
    original_url: str
    short_name: str
    short_url: str
    created_at: datetime
