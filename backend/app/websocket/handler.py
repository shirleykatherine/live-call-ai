"""
WebSocket connection manager and message handler.
Manages all active call sessions and routes messages through the AI agent.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect

from app.agents.graph import run_agent
from app.agents.state import AgentState
from app.database import SessionLocal
from app.models.call import Call, Transcript
from app.schemas.agent import AgentAnalysis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections, keyed by call_id."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.call_states: dict[str, AgentState] = {}

    async def connect(self, call_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[call_id] = websocket
        logger.info(f"WS connected: call_id={call_id}")

    def disconnect(self, call_id: str):
        self.active_connections.pop(call_id, None)
        logger.info(f"WS disconnected: call_id={call_id}")

    async def send_json(self, call_id: str, message: dict):
        ws = self.active_connections.get(call_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS message to {call_id}: {e}")

    def get_or_create_state(self, call_id: str, customer_id: Optional[str] = None) -> AgentState:
        if call_id not in self.call_states:
            self.call_states[call_id] = AgentState(
                call_id=call_id,
                customer_id=customer_id,
                transcript=[],
                latest_speaker="customer",
                latest_text="",
                intent=None,
                intent_confidence=None,
                sentiment=None,
                sentiment_confidence=None,
                conversation_stage=None,
                key_entities=[],
                requires_tool_call=False,
                required_tool=None,
                tool_parameters=None,
                tool_calls_made=[],
                retrieved_knowledge=[],
                customer_info=None,
                order_info=None,
                next_best_action=None,
                action_priority=None,
                action_rationale=None,
                suggested_response=None,
                error=None,
                node_errors=[],
                tool_call_count=0,
            )
        return self.call_states[call_id]

    def update_state(self, call_id: str, state: AgentState):
        self.call_states[call_id] = state

    def clear_state(self, call_id: str):
        self.call_states.pop(call_id, None)


# Global singleton
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, call_id: str):
    """Main WebSocket handler for a call session."""
    await manager.connect(call_id, websocket)

    # Send initial connection confirmation
    await manager.send_json(call_id, {
        "type": "status",
        "data": {
            "status": "connected",
            "call_id": call_id,
            "message": "Co-pilot connected and ready.",
            "timestamp": datetime.utcnow().isoformat(),
        },
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(call_id, {
                    "type": "error",
                    "data": {"message": "Invalid JSON received."},
                })
                continue

            msg_type = message.get("type")

            if msg_type == "transcript":
                await _handle_transcript_message(call_id, message.get("data", {}))

            elif msg_type == "ping":
                await manager.send_json(call_id, {
                    "type": "pong",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                })

            elif msg_type == "end_call":
                await _handle_end_call(call_id)
                break

            else:
                logger.warning(f"Unknown WS message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {call_id}")
    except Exception as e:
        logger.error(f"WS handler error for {call_id}: {e}")
        await manager.send_json(call_id, {
            "type": "error",
            "data": {"message": f"An error occurred: {str(e)}"},
        })
    finally:
        manager.disconnect(call_id)


async def _handle_transcript_message(call_id: str, data: dict):
    """Process a new transcript turn and run the AI agent."""
    speaker = data.get("speaker", "customer")
    text = data.get("text", "").strip()
    customer_id = data.get("customer_id")

    if not text:
        return

    timestamp = datetime.utcnow().isoformat()

    # Persist transcript to database
    db = SessionLocal()
    try:
        db_transcript = Transcript(
            call_id=call_id,
            speaker=speaker,
            text=text,
            timestamp=datetime.utcnow(),
        )
        db.add(db_transcript)
        db.commit()
        db.refresh(db_transcript)
        transcript_id = db_transcript.id
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")
        transcript_id = None
    finally:
        db.close()

    # Echo transcript back to the dashboard immediately (before AI processes it)
    await manager.send_json(call_id, {
        "type": "transcript",
        "data": {
            "id": transcript_id,
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp,
        },
    })

    # Only run AI analysis on customer turns (or when agent says something notable)
    if speaker not in ("customer", "agent"):
        return

    # Update conversation state
    state = manager.get_or_create_state(call_id, customer_id)
    state["latest_speaker"] = speaker
    state["latest_text"] = text
    state["transcript"] = state["transcript"] + [{
        "speaker": speaker,
        "text": text,
        "timestamp": timestamp,
    }]
    state["tool_call_count"] = 0  # Reset per turn

    # Signal to frontend that AI is thinking
    await manager.send_json(call_id, {
        "type": "status",
        "data": {"status": "analyzing", "message": "Analyzing conversation..."},
    })

    # Run the LangGraph agent
    try:
        result_state = await run_agent(state)
        manager.update_state(call_id, result_state)

        # Build the analysis payload for the frontend
        analysis: dict = {
            "intent": result_state.get("intent", "general_inquiry"),
            "intent_confidence": result_state.get("intent_confidence", 0.5),
            "sentiment": result_state.get("sentiment", "neutral"),
            "sentiment_confidence": result_state.get("sentiment_confidence", 0.5),
            "conversation_stage": result_state.get("conversation_stage", "problem_identification"),
            "key_entities": result_state.get("key_entities", []),
            "next_best_action": result_state.get("next_best_action", "ask_clarifying_question"),
            "action_priority": result_state.get("action_priority", "medium"),
            "action_rationale": result_state.get("action_rationale", ""),
            "suggested_response": result_state.get("suggested_response", ""),
            "retrieved_knowledge": result_state.get("retrieved_knowledge", []),
            "tool_calls_made": result_state.get("tool_calls_made", []),
            "customer_info": result_state.get("customer_info"),
            "order_info": result_state.get("order_info"),
            "error": result_state.get("error"),
        }

        await manager.send_json(call_id, {
            "type": "analysis",
            "data": analysis,
        })

        # Update DB transcript with analysis
        if transcript_id:
            db = SessionLocal()
            try:
                t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
                if t:
                    t.detected_intent = result_state.get("intent")
                    t.detected_sentiment = result_state.get("sentiment")
                    t.conversation_stage = result_state.get("conversation_stage")
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to update transcript analysis: {e}")
            finally:
                db.close()

    except Exception as e:
        logger.error(f"Agent run failed for {call_id}: {e}")
        await manager.send_json(call_id, {
            "type": "analysis",
            "data": {
                "intent": "general_inquiry",
                "sentiment": "neutral",
                "next_best_action": "ask_clarifying_question",
                "suggested_response": "Thank you for your patience. How can I help you today?",
                "error": str(e),
            },
        })

    await manager.send_json(call_id, {
        "type": "status",
        "data": {"status": "ready", "message": "Ready"},
    })


async def _handle_end_call(call_id: str):
    """Handle call end — trigger summary generation."""
    from app.services.summary_service import generate_call_summary

    state = manager.call_states.get(call_id)
    transcript = state.get("transcript", []) if state else []
    intent = state.get("intent", "unknown") if state else "unknown"
    sentiment = state.get("sentiment", "unknown") if state else "unknown"
    tools_used = [tc["tool_name"] for tc in (state.get("tool_calls_made") or [])] if state else []

    await manager.send_json(call_id, {
        "type": "status",
        "data": {"status": "generating_summary", "message": "Generating call summary..."},
    })

    summary = None
    if transcript:
        summary = await generate_call_summary(
            transcript=transcript,
            intent=intent,
            sentiment=sentiment,
            tools_used=list(set(tools_used)),
        )

    # Persist summary to DB
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.status = "ended"
            call.ended_at = datetime.utcnow()
            if call.started_at:
                delta = call.ended_at - call.started_at
                call.duration_seconds = int(delta.total_seconds())
            if summary:
                call.summary_issue = summary.issue
                call.summary_resolution = summary.resolution
                call.summary_actions_taken = json.dumps(summary.actions_taken)
                call.summary_follow_up = summary.follow_up_description or ""
                call.summary_sentiment = summary.customer_sentiment_overall
                call.summary_escalated = str(summary.escalated)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to save call summary to DB: {e}")
    finally:
        db.close()

    summary_data = {}
    if summary:
        summary_data = {
            "issue": summary.issue,
            "intent": summary.intent,
            "resolution": summary.resolution,
            "actions_taken": summary.actions_taken,
            "follow_up_required": summary.follow_up_required,
            "follow_up_description": summary.follow_up_description,
            "customer_sentiment_overall": summary.customer_sentiment_overall,
            "escalated": summary.escalated,
            "escalation_reason": summary.escalation_reason,
            "key_information": summary.key_information,
        }

    await manager.send_json(call_id, {
        "type": "summary",
        "data": {
            "call_id": call_id,
            "summary": summary_data,
            "transcript_count": len(transcript),
        },
    })

    manager.clear_state(call_id)
