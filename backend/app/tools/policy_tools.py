"""
Policy search tool — wraps the RAG retriever for use in tool calls.
"""
import logging
from app.rag.retriever import retrieve_relevant_knowledge

logger = logging.getLogger(__name__)


def search_policy(query: str, n_results: int = 3) -> dict:
    """
    Search the company knowledge base for policy information relevant to the query.
    Uses semantic search (RAG) over all policy documents.
    """
    try:
        results = retrieve_relevant_knowledge(query, n_results=n_results)
        if not results:
            return {
                "success": True,
                "data": {
                    "query": query,
                    "results": [],
                    "message": "No relevant policy information found for this query.",
                },
            }
        return {
            "success": True,
            "data": {
                "query": query,
                "results": results,
            },
        }
    except Exception as e:
        logger.error(f"search_policy error: {e}")
        return {"success": False, "error": str(e), "data": None}
