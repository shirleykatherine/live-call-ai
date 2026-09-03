"""REST API routes for call management."""
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.call import Call
from app.schemas.call import CallCreate, CallOut, CallSummaryOut, TranscriptOut, ActionItemOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/", response_model=CallOut)
def start_call(data: CallCreate, db: Session = Depends(get_db)):
    """Start a new call session."""
    call = Call(
        customer_id=data.customer_id,
        status="active",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    logger.info(f"Call started: {call.id}")
    return call


@router.get("/", response_model=list[CallOut])
def list_calls(limit: int = 20, db: Session = Depends(get_db)):
    """List recent calls."""
    calls = db.query(Call).order_by(Call.started_at.desc()).limit(limit).all()
    return calls


@router.get("/{call_id}", response_model=CallSummaryOut)
def get_call(call_id: str, db: Session = Depends(get_db)):
    """Get full call details including transcript and action items."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found.")
    return call


@router.post("/{call_id}/end")
def end_call(call_id: str, db: Session = Depends(get_db)):
    """Mark a call as ended (REST fallback — use WebSocket 'end_call' message)."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found.")
    if call.status == "ended":
        return {"message": "Call already ended.", "call_id": call_id}

    call.status = "ended"
    call.ended_at = datetime.utcnow()
    if call.started_at:
        delta = call.ended_at - call.started_at
        call.duration_seconds = int(delta.total_seconds())
    db.commit()
    return {"message": "Call ended.", "call_id": call_id}
