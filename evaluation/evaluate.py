"""
Evaluation script for the Live Call Co-pilot AI pipeline.

Runs predefined test scenarios through the LangGraph agent and measures:
- Intent classification accuracy
- Sentiment classification accuracy
- Tool call correctness
- Next Best Action relevance
- Average latency

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --json     # JSON output for API
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agents.graph import run_agent
from app.agents.state import AgentState
from app.database import init_db
from app.rag.ingestion import ingest_knowledge_base


DATASET_PATH = Path(__file__).parent / "datasets" / "test_conversations.json"


def build_initial_state(scenario: dict) -> AgentState:
    """Build the AgentState from a test scenario."""
    transcript = []
    for turn in scenario["conversation"]:
        transcript.append({
            "speaker": turn["speaker"],
            "text": turn["text"],
            "timestamp": datetime.utcnow().isoformat(),
        })

    last_turn = scenario["conversation"][-1]
    return AgentState(
        call_id=f"eval-{scenario['id']}",
        customer_id=None,
        transcript=transcript,
        latest_speaker=last_turn["speaker"],
        latest_text=last_turn["text"],
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


async def run_scenario(scenario: dict) -> dict:
    """Run one scenario and return evaluation results."""
    expected = scenario["expected"]
    state = build_initial_state(scenario)

    start = time.perf_counter()
    result = await run_agent(state)
    latency_ms = (time.perf_counter() - start) * 1000

    # Extract results
    detected_intent = (result.get("intent") or "").lower()
    detected_sentiment = (result.get("sentiment") or "").lower()
    next_best_action = (result.get("next_best_action") or "").lower()
    tools_called = [tc["tool_name"] for tc in (result.get("tool_calls_made") or [])]
    has_error = bool(result.get("error"))

    # Evaluate each metric
    intent_correct = int(expected["intent"].lower() in detected_intent or detected_intent in expected["intent"].lower())
    sentiment_correct = int(expected["sentiment"].lower() in detected_sentiment or detected_sentiment in expected["sentiment"].lower())
    nba_correct = int(expected.get("next_best_action_contains", "").lower() in next_best_action)

    expected_tool = expected.get("expected_tool")
    if expected_tool:
        tool_correct = int(expected_tool in tools_called)
    else:
        tool_correct = int(len(tools_called) == 0 or not expected.get("requires_tool", False))

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "latency_ms": round(latency_ms, 1),
        "detected_intent": detected_intent,
        "expected_intent": expected["intent"],
        "intent_correct": intent_correct,
        "detected_sentiment": detected_sentiment,
        "expected_sentiment": expected["sentiment"],
        "sentiment_correct": sentiment_correct,
        "next_best_action": next_best_action,
        "nba_correct": nba_correct,
        "tools_called": tools_called,
        "tool_correct": tool_correct,
        "has_error": has_error,
        "error": result.get("error"),
        "suggested_response": result.get("suggested_response", ""),
    }


async def run_evaluation(json_output: bool = False):
    """Run the full evaluation suite."""
    if not json_output:
        print("\n" + "=" * 60)
        print("  Live Call Co-pilot — Evaluation Suite")
        print("=" * 60)

    # Initialize systems
    if not json_output:
        print("\nInitializing database and knowledge base...")
    init_db()
    ingest_knowledge_base()

    # Load dataset
    with open(DATASET_PATH) as f:
        scenarios = json.load(f)

    if not json_output:
        print(f"Running {len(scenarios)} evaluation scenarios...\n")

    results = []
    for scenario in scenarios:
        if not json_output:
            print(f"  [{scenario['id']}] {scenario['name']}...", end=" ", flush=True)
        try:
            result = await run_scenario(scenario)
            results.append(result)
            if not json_output:
                status = "PASS" if all([
                    result["intent_correct"],
                    result["sentiment_correct"],
                ]) else "PARTIAL"
                print(f"{status} ({result['latency_ms']:.0f}ms)")
        except Exception as e:
            results.append({
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "error": str(e),
                "intent_correct": 0,
                "sentiment_correct": 0,
                "nba_correct": 0,
                "tool_correct": 0,
                "latency_ms": 0,
            })
            if not json_output:
                print(f"ERROR: {e}")

    # Compute summary metrics
    n = len(results)
    metrics = {
        "total_scenarios": n,
        "intent_accuracy": round(sum(r.get("intent_correct", 0) for r in results) / n * 100, 1),
        "sentiment_accuracy": round(sum(r.get("sentiment_correct", 0) for r in results) / n * 100, 1),
        "nba_accuracy": round(sum(r.get("nba_correct", 0) for r in results) / n * 100, 1),
        "tool_call_accuracy": round(sum(r.get("tool_correct", 0) for r in results) / n * 100, 1),
        "avg_latency_ms": round(sum(r.get("latency_ms", 0) for r in results) / n, 1),
        "error_rate": round(sum(1 for r in results if r.get("has_error")) / n * 100, 1),
        "run_timestamp": datetime.utcnow().isoformat(),
    }

    output = {"metrics": metrics, "results": results, "success": True}

    if json_output:
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "-" * 60)
        print("  RESULTS SUMMARY")
        print("-" * 60)
        print(f"  Intent Accuracy:      {metrics['intent_accuracy']}%")
        print(f"  Sentiment Accuracy:   {metrics['sentiment_accuracy']}%")
        print(f"  NBA Accuracy:         {metrics['nba_accuracy']}%")
        print(f"  Tool Call Accuracy:   {metrics['tool_call_accuracy']}%")
        print(f"  Avg Latency:          {metrics['avg_latency_ms']} ms")
        print(f"  Error Rate:           {metrics['error_rate']}%")
        print("=" * 60 + "\n")

    return output


if __name__ == "__main__":
    json_mode = "--json" in sys.argv
    asyncio.run(run_evaluation(json_output=json_mode))
