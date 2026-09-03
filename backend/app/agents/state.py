"""
LangGraph agent state definition.
All nodes read from and write to this shared state.
"""
from typing import Optional, Annotated
from typing_extensions import TypedDict
import operator


class TranscriptTurn(TypedDict):
    speaker: str   # "customer" | "agent"
    text: str
    timestamp: str


class ToolCallRecord(TypedDict):
    tool_name: str
    parameters: dict
    result: dict
    success: bool


class AgentState(TypedDict):
    """Shared state flowing through the LangGraph pipeline."""

    # -- Call context --
    call_id: str
    customer_id: Optional[str]

    # -- Conversation --
    transcript: list[TranscriptTurn]  # Full conversation history
    latest_speaker: str
    latest_text: str

    # -- Analysis results --
    intent: Optional[str]
    intent_confidence: Optional[float]
    sentiment: Optional[str]
    sentiment_confidence: Optional[float]
    conversation_stage: Optional[str]
    key_entities: list[str]

    # -- Tool decision --
    requires_tool_call: bool
    required_tool: Optional[str]
    tool_parameters: Optional[dict]

    # -- Tool results --
    tool_calls_made: Annotated[list[ToolCallRecord], operator.add]

    # -- Retrieved knowledge --
    retrieved_knowledge: list[dict]

    # -- Customer / order data from tools --
    customer_info: Optional[dict]
    order_info: Optional[dict]

    # -- Output --
    next_best_action: Optional[str]
    action_priority: Optional[str]
    action_rationale: Optional[str]
    suggested_response: Optional[str]

    # -- Error handling --
    error: Optional[str]
    node_errors: Annotated[list[str], operator.add]

    # -- Control flow --
    tool_call_count: int   # Prevent infinite tool loops
