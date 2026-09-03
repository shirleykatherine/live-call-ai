"""
LangGraph agent nodes.
Each function takes AgentState and returns a partial state update dict.
"""
import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from app.agents.prompts import (
    INTENT_SENTIMENT_PROMPT,
    NEXT_BEST_ACTION_PROMPT,
)
from app.agents.state import AgentState
from app.config import get_settings
from app.rag.retriever import retrieve_relevant_knowledge, format_knowledge_for_prompt
from app.schemas.agent import IntentSentimentAnalysis, NextBestAction
from app.tools.customer_tools import get_customer
from app.tools.order_tools import (
    get_order_status,
    get_customer_orders,
    get_available_resolution_options,
)
from app.tools.policy_tools import search_policy
from app.tools.ticket_tools import create_support_ticket

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_TOOL_CALLS = 3  # Safety limit per conversation turn


def _get_llm() -> ChatOpenAI:
    """Build the LLM client from config."""
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


def _format_transcript(transcript: list[dict]) -> str:
    """Format conversation history for prompts."""
    if not transcript:
        return "No conversation yet."

    lines = []

    for turn in transcript[-10:]:
        speaker = turn.get("speaker", "unknown").capitalize()
        text = turn.get("text", "")
        lines.append(f"{speaker}: {text}")

    return "\n".join(lines)


def _safe_json_parse(text: str, schema_class) -> Any:
    """
    Attempt to parse LLM output as JSON and validate against a Pydantic schema.
    Returns None if parsing fails.
    """
    try:
        text = text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]

            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text.strip())

        return schema_class(**data)

    except Exception as e:
        logger.warning(
            f"JSON parse failed: {e}. Raw text: {text[:200]}"
        )
        return None


# =============================================================================
# Node: update_state
# =============================================================================

def update_state_node(state: AgentState) -> dict:
    """
    Entry node: initialize default values and validate state.
    """
    return {
        "tool_call_count": state.get("tool_call_count", 0),
        "tool_calls_made": [],
        "node_errors": [],
        "retrieved_knowledge": state.get("retrieved_knowledge", []),
        "key_entities": state.get("key_entities", []),
    }


# =============================================================================
# Node: analyze_intent_sentiment
# =============================================================================

def analyze_intent_sentiment_node(state: AgentState) -> dict:
    """
    Analyze customer intent, sentiment, conversation stage,
    and decide if a tool call is needed.
    """
    try:
        llm = _get_llm()

        structured_llm = llm.with_structured_output(
            IntentSentimentAnalysis,
            method="function_calling",
        )

        conversation_history = _format_transcript(
            state.get("transcript", [])
        )

        prompt = INTENT_SENTIMENT_PROMPT.format(
            conversation_history=conversation_history,
            latest_speaker=state.get(
                "latest_speaker",
                "customer",
            ),
            latest_text=state.get(
                "latest_text",
                "",
            ),
        )

        analysis: IntentSentimentAnalysis = structured_llm.invoke(prompt)

        # -----------------------------------------------------------------
        # IMPORTANT:
        # Make sure tool parameters are always a dictionary.
        # -----------------------------------------------------------------
        tool_parameters = analysis.tool_parameters or {}

        # -----------------------------------------------------------------
        # IMPORTANT:
        # If get_customer is requested but customer_id was not supplied
        # by the LLM, use the customer_id already present in AgentState.
        #
        # This fixes:
        # get_customer() missing 1 required positional argument:
        # 'customer_id'
        # -----------------------------------------------------------------
        if analysis.required_tool == "get_customer":

            state_customer_id = state.get("customer_id")

            if (
                "customer_id" not in tool_parameters
                or not tool_parameters.get("customer_id")
            ):
                if state_customer_id:
                    tool_parameters["customer_id"] = state_customer_id

            # If there is still no customer ID, do not execute the tool.
            if not tool_parameters.get("customer_id"):
                logger.warning(
                    "get_customer requested but no customer_id is available."
                )

                return {
                    "intent": analysis.intent,
                    "intent_confidence": analysis.intent_confidence,
                    "sentiment": analysis.sentiment,
                    "sentiment_confidence": analysis.sentiment_confidence,
                    "conversation_stage": analysis.conversation_stage,
                    "key_entities": analysis.key_entities,
                    "requires_tool_call": False,
                    "required_tool": None,
                    "tool_parameters": None,
                    "node_errors": [
                        "get_customer requested but no customer_id was available."
                    ],
                }

        return {
            "intent": analysis.intent,
            "intent_confidence": analysis.intent_confidence,
            "sentiment": analysis.sentiment,
            "sentiment_confidence": analysis.sentiment_confidence,
            "conversation_stage": analysis.conversation_stage,
            "key_entities": analysis.key_entities,
            "requires_tool_call": analysis.requires_tool_call,
            "required_tool": analysis.required_tool,
            "tool_parameters": tool_parameters,
        }

    except Exception as e:
        logger.error(
            f"analyze_intent_sentiment_node error: {e}"
        )

        return {
            "intent": "general_inquiry",
            "intent_confidence": 0.5,
            "sentiment": "neutral",
            "sentiment_confidence": 0.5,
            "conversation_stage": "problem_identification",
            "key_entities": [],
            "requires_tool_call": False,
            "required_tool": None,
            "tool_parameters": None,
            "node_errors": [
                f"Intent analysis failed: {str(e)}"
            ],
        }


# =============================================================================
# Node: retrieve_knowledge
# =============================================================================

def retrieve_knowledge_node(state: AgentState) -> dict:
    """
    Semantically retrieve relevant company knowledge
    based on intent and conversation.
    """
    try:
        intent = state.get("intent", "")
        latest_text = state.get("latest_text", "")
        key_entities = state.get("key_entities", [])

        query_parts = [
            intent.replace("_", " ")
        ]

        if latest_text:
            query_parts.append(
                latest_text[:200]
            )

        if key_entities:
            query_parts.append(
                " ".join(key_entities[:3])
            )

        query = " ".join(query_parts)

        chunks = retrieve_relevant_knowledge(
            query,
            n_results=3,
        )

        return {
            "retrieved_knowledge": chunks
        }

    except Exception as e:
        logger.error(
            f"retrieve_knowledge_node error: {e}"
        )

        return {
            "retrieved_knowledge": [],
            "node_errors": [
                f"Knowledge retrieval failed: {str(e)}"
            ],
        }


# =============================================================================
# Node: call_tool
# =============================================================================

TOOL_REGISTRY = {
    "get_customer": get_customer,
    "get_order_status": get_order_status,
    "get_customer_orders": get_customer_orders,
    "get_available_resolution_options": get_available_resolution_options,
    "search_policy": search_policy,
    "create_support_ticket": create_support_ticket,
}


def call_tool_node(state: AgentState) -> dict:
    """
    Execute the tool decided by the analysis node.

    Updates customer_info and order_info from results.
    """
    required_tool = state.get("required_tool")

    tool_parameters = (
        state.get("tool_parameters") or {}
    )

    tool_call_count = state.get(
        "tool_call_count",
        0,
    )

    if not required_tool:
        return {
            "requires_tool_call": False
        }

    if tool_call_count >= MAX_TOOL_CALLS:
        logger.warning(
            f"Tool call limit reached ({MAX_TOOL_CALLS}). Skipping."
        )

        return {
            "requires_tool_call": False,
            "node_errors": [
                "Tool call limit reached for this turn."
            ],
        }

    tool_fn = TOOL_REGISTRY.get(required_tool)

    if not tool_fn:
        logger.error(
            f"Tool '{required_tool}' not found in registry."
        )

        return {
            "requires_tool_call": False,
            "node_errors": [
                f"Unknown tool: {required_tool}"
            ],
        }

    # ---------------------------------------------------------------------
    # SAFETY CHECKS FOR REQUIRED TOOL PARAMETERS
    # ---------------------------------------------------------------------

    if required_tool == "get_customer":

        customer_id = tool_parameters.get(
            "customer_id"
        )

        # Fall back to AgentState customer_id
        if not customer_id:
            customer_id = state.get(
                "customer_id"
            )

            if customer_id:
                tool_parameters["customer_id"] = customer_id

        # Never call get_customer without an ID.
        if not customer_id:
            logger.warning(
                "Skipping get_customer because customer_id is missing."
            )

            return {
                "requires_tool_call": False,
                "node_errors": [
                    "Cannot call get_customer without customer_id."
                ],
            }

    # ---------------------------------------------------------------------
    # Execute tool
    # ---------------------------------------------------------------------

    try:
        logger.info(
            f"Executing tool '{required_tool}' "
            f"with parameters: {tool_parameters}"
        )

        result = tool_fn(
            **tool_parameters
        )

        # Make sure result is a dictionary.
        if not isinstance(result, dict):
            result = {
                "success": False,
                "error": "Tool returned an invalid result.",
                "data": None,
            }

        record = {
            "tool_name": required_tool,
            "parameters": tool_parameters,
            "result": result,
            "success": result.get(
                "success",
                False,
            ),
        }

        updates: dict = {
            "tool_calls_made": [record],
            "tool_call_count": tool_call_count + 1,
            "requires_tool_call": False,
        }

        # -----------------------------------------------------------------
        # Extract useful data into state
        # -----------------------------------------------------------------

        data = result.get("data")

        if data and result.get("success"):

            if required_tool == "get_customer":

                updates["customer_info"] = data

            elif required_tool in (
                "get_order_status",
                "get_available_resolution_options",
            ):

                updates["order_info"] = data

            elif required_tool == "get_customer_orders":

                updates["order_info"] = data

            elif required_tool == "search_policy":

                policy_chunks = data.get(
                    "results",
                    [],
                )

                existing = state.get(
                    "retrieved_knowledge",
                    [],
                )

                combined = {
                    c["content"]: c
                    for c in (
                        existing + policy_chunks
                    )
                }

                updates["retrieved_knowledge"] = list(
                    combined.values()
                )[:5]

        return updates

    except Exception as e:

        logger.error(
            f"Tool '{required_tool}' execution error: {e}"
        )

        return {
            "tool_calls_made": [
                {
                    "tool_name": required_tool,
                    "parameters": tool_parameters,
                    "result": {
                        "error": str(e)
                    },
                    "success": False,
                }
            ],
            "requires_tool_call": False,
            "node_errors": [
                f"Tool {required_tool} failed: {str(e)}"
            ],
        }


# =============================================================================
# Node: generate_nba_and_response
# =============================================================================

def generate_nba_response_node(
    state: AgentState
) -> dict:
    """
    Generate the Next Best Action and a suggested agent response.
    """
    try:
        llm = _get_llm()

        structured_llm = llm.with_structured_output(
            NextBestAction,
            method="function_calling",
        )

        conversation_history = _format_transcript(
            state.get("transcript", [])
        )

        retrieved_knowledge = format_knowledge_for_prompt(
            state.get(
                "retrieved_knowledge",
                [],
            )
        )

        # Format tool results for prompt
        tool_results_parts = []

        for tc in state.get(
            "tool_calls_made",
            [],
        ):

            if (
                tc.get("success")
                and tc.get("result", {}).get("data")
            ):

                tool_results_parts.append(
                    f"[{tc['tool_name']}]\n"
                    f"{json.dumps(tc['result']['data'], indent=2)}"
                )

        tool_results = (
            "\n\n".join(tool_results_parts)
            if tool_results_parts
            else "No tool calls made."
        )

        customer_info = state.get(
            "customer_info"
        )

        customer_info_str = (
            json.dumps(
                customer_info,
                indent=2,
            )
            if customer_info
            else "Customer not yet identified."
        )

        prompt = NEXT_BEST_ACTION_PROMPT.format(
            intent=state.get(
                "intent",
                "unknown",
            ),
            intent_confidence=state.get(
                "intent_confidence",
                0.0,
            ),
            sentiment=state.get(
                "sentiment",
                "unknown",
            ),
            conversation_stage=state.get(
                "conversation_stage",
                "unknown",
            ),
            key_entities=", ".join(
                state.get(
                    "key_entities",
                    [],
                )
            ) or "none",
            conversation_history=conversation_history,
            retrieved_knowledge=retrieved_knowledge,
            tool_results=tool_results,
            customer_info=customer_info_str,
        )

        nba: NextBestAction = structured_llm.invoke(
            prompt
        )

        return {
            "next_best_action": nba.action,
            "action_priority": nba.priority,
            "action_rationale": nba.rationale,
            "suggested_response": nba.suggested_response,
            "error": None,
        }

    except Exception as e:

        logger.error(
            f"generate_nba_response_node error: {e}"
        )

        return {
            "next_best_action": "ask_clarifying_question",
            "action_priority": "medium",
            "action_rationale": (
                "Unable to determine NBA due to "
                "a processing error."
            ),
            "suggested_response": (
                "Thank you for your patience. "
                "Could you please provide more details "
                "so I can better assist you?"
            ),
            "error": str(e),
            "node_errors": [
                f"NBA generation failed: {str(e)}"
            ],
        }