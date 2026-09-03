"""
Post-call summary generation service.
Uses the LLM to produce a structured summary from the full call transcript.
"""
import logging
import json
from app.agents.prompts import CALL_SUMMARY_PROMPT
from app.schemas.agent import CallSummaryGenerated
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


async def generate_call_summary(
    transcript: list[dict],
    intent: str = "unknown",
    sentiment: str = "unknown",
    tools_used: list[str] = None,
) -> CallSummaryGenerated | None:
    """
    Generate a structured post-call summary using the LLM.
    Returns None if generation fails.
    """
    if not transcript:
        logger.warning("Cannot generate summary: empty transcript.")
        return None

    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(CallSummaryGenerated)

        # Format transcript for prompt
        transcript_lines = []
        for turn in transcript:
            speaker = turn.get("speaker", "unknown").capitalize()
            text = turn.get("text", "")
            timestamp = turn.get("timestamp", "")
            transcript_lines.append(f"[{timestamp}] {speaker}: {text}")

        transcript_str = "\n".join(transcript_lines)
        tools_str = ", ".join(tools_used) if tools_used else "none"

        prompt = CALL_SUMMARY_PROMPT.format(
            transcript=transcript_str,
            intent=intent,
            sentiment=sentiment,
            tools_used=tools_str,
        )

        summary: CallSummaryGenerated = await structured_llm.ainvoke(prompt)
        logger.info("Post-call summary generated successfully.")
        return summary

    except Exception as e:
        logger.error(f"Failed to generate call summary: {e}")
        return None
