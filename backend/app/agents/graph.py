"""
LangGraph StateGraph definition for the Live Call Co-pilot.

Graph flow:
  START
    → update_state
    → analyze_intent_sentiment
    → retrieve_knowledge
    → [conditional] call_tool  (if tool needed)
    → generate_nba_response
  END
"""
import logging
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.nodes import (
    update_state_node,
    analyze_intent_sentiment_node,
    retrieve_knowledge_node,
    call_tool_node,
    generate_nba_response_node,
)

logger = logging.getLogger(__name__)


def _should_call_tool(state: AgentState) -> str:
    """
    Conditional edge: route to tool calling or directly to NBA generation.
    Prevents infinite loops via tool_call_count.
    """
    if state.get("requires_tool_call") and state.get("required_tool"):
        if state.get("tool_call_count", 0) < 3:
            return "call_tool"
    return "generate_nba_response"


def build_agent_graph() -> StateGraph:
    """Construct and compile the LangGraph agent workflow."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("update_state", update_state_node)
    graph.add_node("analyze_intent_sentiment", analyze_intent_sentiment_node)
    graph.add_node("retrieve_knowledge", retrieve_knowledge_node)
    graph.add_node("call_tool", call_tool_node)
    graph.add_node("generate_nba_response", generate_nba_response_node)

    # Wire edges
    graph.add_edge(START, "update_state")
    graph.add_edge("update_state", "analyze_intent_sentiment")
    graph.add_edge("analyze_intent_sentiment", "retrieve_knowledge")

    # Conditional: tool call or skip to NBA
    graph.add_conditional_edges(
        "retrieve_knowledge",
        _should_call_tool,
        {
            "call_tool": "call_tool",
            "generate_nba_response": "generate_nba_response",
        },
    )

    # After tool call, decide again (allows one re-analysis if needed)
    graph.add_edge("call_tool", "generate_nba_response")
    graph.add_edge("generate_nba_response", END)

    return graph.compile()


# Module-level compiled graph singleton
_compiled_graph = None


def get_compiled_graph():
    """Return the compiled graph, building it if necessary."""
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Compiling LangGraph agent graph...")
        _compiled_graph = build_agent_graph()
        logger.info("LangGraph agent graph compiled.")
    return _compiled_graph


async def run_agent(state: AgentState) -> AgentState:
    """
    Run the agent graph for one conversation turn.
    Returns the final state after all nodes have executed.
    """
    graph = get_compiled_graph()
    try:
        result = await graph.ainvoke(state)
        return result
    except Exception as e:
        logger.error(f"Agent graph execution error: {e}")
        # Return state with error — never crash the caller
        return {
            **state,
            "error": str(e),
            "next_best_action": "ask_clarifying_question",
            "action_priority": "medium",
            "action_rationale": "AI processing error. Please proceed manually.",
            "suggested_response": "Thank you for contacting us. Let me look into this for you.",
        }
