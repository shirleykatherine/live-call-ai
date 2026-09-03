"""Pydantic schemas for AI agent structured outputs."""
from typing import Optional
from pydantic import BaseModel, Field


class IntentSentimentAnalysis(BaseModel):
    """Structured output from the intent/sentiment analysis node."""
    intent: str = Field(
        description=(
            "Primary customer intent. One of: order_status, refund_request, "
            "cancellation, product_issue, payment_issue, account_issue, "
            "complaint, technical_problem, general_inquiry, delivery_issue, "
            "return_request, exchange_request, escalation"
        )
    )
    intent_confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    sentiment: str = Field(
        description=(
            "Customer emotional tone. One of: positive, neutral, frustrated, "
            "angry, urgent, satisfied, confused"
        )
    )
    sentiment_confidence: float = Field(ge=0.0, le=1.0)
    conversation_stage: str = Field(
        description=(
            "Current stage. One of: greeting, problem_identification, "
            "information_gathering, resolution, escalation, closing"
        )
    )
    key_entities: list[str] = Field(
        default_factory=list,
        description="Extracted entities like order IDs, product names, dates",
    )
    requires_tool_call: bool = Field(
        description="Whether a tool call is needed to proceed"
    )
    required_tool: Optional[str] = Field(
        default=None,
        description="Tool name if requires_tool_call is True",
    )
    tool_parameters: Optional[dict] = Field(
        default=None,
        description="Parameters to pass to the tool",
    )


class NextBestAction(BaseModel):
    """Structured output for the Next Best Action recommendation."""
    action: str = Field(
        description=(
            "The recommended action. One of: ask_for_order_number, "
            "verify_customer_identity, check_order_status, search_policy, "
            "offer_refund, offer_replacement, escalate_to_supervisor, "
            "create_support_ticket, explain_options, close_conversation, "
            "ask_clarifying_question, provide_tracking_info, "
            "process_cancellation, process_return"
        )
    )
    priority: str = Field(description="urgent | high | medium | low")
    rationale: str = Field(description="1-2 sentence explanation of why this action")
    suggested_response: str = Field(
        description="Natural language response the agent can say to the customer"
    )


class AgentAnalysis(BaseModel):
    """Full AI analysis result sent to the frontend dashboard."""
    intent: str
    intent_confidence: float
    sentiment: str
    sentiment_confidence: float
    conversation_stage: str
    key_entities: list[str]
    next_best_action: str
    action_priority: str
    action_rationale: str
    suggested_response: str
    retrieved_knowledge: list[dict] = Field(default_factory=list)
    tool_calls_made: list[dict] = Field(default_factory=list)
    customer_info: Optional[dict] = None
    order_info: Optional[dict] = None
    error: Optional[str] = None


class CallSummaryGenerated(BaseModel):
    """Structured post-call summary from the LLM."""
    issue: str = Field(description="The main customer issue in 1-2 sentences")
    intent: str = Field(description="Primary intent identified")
    resolution: str = Field(description="How the issue was resolved or current status")
    actions_taken: list[str] = Field(description="List of concrete actions taken during the call")
    follow_up_required: bool
    follow_up_description: Optional[str] = Field(default=None)
    customer_sentiment_overall: str
    escalated: bool
    escalation_reason: Optional[str] = Field(default=None)
    key_information: list[str] = Field(
        description="Important facts gathered during the call"
    )
