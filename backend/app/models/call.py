"""ORM models for calls, transcripts, and action items."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    status = Column(
        Enum("active", "ended", "error", name="call_status"),
        default="active",
        nullable=False,
    )
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Post-call summary fields
    summary_issue = Column(Text, nullable=True)
    summary_resolution = Column(Text, nullable=True)
    summary_actions_taken = Column(Text, nullable=True)
    summary_follow_up = Column(Text, nullable=True)
    summary_sentiment = Column(String, nullable=True)
    summary_escalated = Column(String, nullable=True)

    # Relationships
    transcripts = relationship("Transcript", back_populates="call", order_by="Transcript.timestamp")
    action_items = relationship("ActionItem", back_populates="call")
    customer = relationship("Customer", back_populates="calls")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    speaker = Column(Enum("customer", "agent", "system", name="speaker_type"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # AI analysis snapshot at this point in conversation
    detected_intent = Column(String, nullable=True)
    detected_sentiment = Column(String, nullable=True)
    conversation_stage = Column(String, nullable=True)

    call = relationship("Call", back_populates="transcripts")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        Enum("pending", "completed", "cancelled", name="action_status"),
        default="pending",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    call = relationship("Call", back_populates="action_items")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, nullable=False)
    scenario_id = Column(String, nullable=False)
    intent_correct = Column(Integer, nullable=True)  # 1 or 0
    sentiment_correct = Column(Integer, nullable=True)
    nba_correct = Column(Integer, nullable=True)
    tool_called_correct = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
