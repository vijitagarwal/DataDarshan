"""Pydantic request models."""
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    query: str
    conversation_history: list[ChatMessage] = []
    table_name: str = "sales"
