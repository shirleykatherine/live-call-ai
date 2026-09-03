"""Pydantic schemas for call-related API endpoints and WebSocket messages."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# --- Transcript ------------------------------------------------------------

class TranscriptCreate(BaseModel):
    speaker: str  # "customer" | "agent" | "system"
    text: str


class TranscriptOut(BaseModel):
    id: str
    call_id: str
    speaker: str
    text: str
    timestamp: datetime
    detected_intent: Optional[str] = None
    detected_sentiment: Optional[str] = None
    conversation_stage: Optional[str] = None

    class Config:
        from_attributes = True


# --- Action Item -----------------------------------------------------------

class ActionItemOut(BaseModel):
    id: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Call ------------------------------------------------------------------

class CallCreate(BaseModel):
    customer_id: Optional[str] = None


class CallOut(BaseModel):
    id: str
    customer_id: Optional[str] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class CallSummaryOut(BaseModel):
    id: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    summary_issue: Optional[str] = None
    summary_resolution: Optional[str] = None
    summary_actions_taken: Optional[str] = None
    summary_follow_up: Optional[str] = None
    summary_sentiment: Optional[str] = None
    summary_escalated: Optional[str] = None
    transcripts: list[TranscriptOut] = []
    action_items: list[ActionItemOut] = []

    class Config:
        from_attributes = True


# --- WebSocket messages ----------------------------------------------------

class WSMessage(BaseModel):
    """Message sent/received over the WebSocket."""
    type: str  # "transcript", "analysis", "status", "error", "summary"
    data: dict
