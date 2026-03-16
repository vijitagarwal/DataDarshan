"""Pydantic response models."""
from pydantic import BaseModel
from typing import Any


class QueryResponse(BaseModel):
    sql: str = ""
    chart_type: str = "bar"
    chart_config: dict[str, Any] = {}
    data: list[dict[str, Any]] = []
    explanation: str = ""
    follow_ups: list[str] = []
    error: str | None = None
