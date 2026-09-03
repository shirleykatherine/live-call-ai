"""
RAG retriever — semantic search over the ChromaDB knowledge base.
"""
import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.rag.embeddings import embed_query

logger = logging.getLogger(__name__)
settings = get_settings()

_chroma_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def retrieve_relevant_knowledge(
    query: str,
    n_results: int = 3,
    score_threshold: float = 0.35,
) -> list[dict]:
    """
    Retrieve relevant knowledge base chunks for a given query.

    Returns a list of dicts with keys:
      - content: str — the chunk text
      - source: str — the document source name
      - file: str — the filename
      - score: float — similarity score (higher = more relevant)
    """
    if not query.strip():
        return []

    try:
        client = _get_client()
        collection = client.get_collection(settings.vector_db_collection)

        if collection.count() == 0:
            logger.warning("Knowledge base is empty. Run ingestion first.")
            return []

        query_embedding = embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, distance in zip(documents, metadatas, distances):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - distance/2
            similarity = 1.0 - (distance / 2.0)

            if similarity >= score_threshold:
                retrieved.append({
                    "content": doc,
                    "source": meta.get("source", "Unknown"),
                    "file": meta.get("file", ""),
                    "score": round(similarity, 3),
                })

        logger.debug(f"Retrieved {len(retrieved)} knowledge chunks for query: '{query[:50]}...'")
        return retrieved

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []


def format_knowledge_for_prompt(chunks: list[dict]) -> str:
    """Format retrieved knowledge chunks into a prompt-ready string."""
    if not chunks:
        return "No relevant company policy found."

    parts = []
    for chunk in chunks:
        parts.append(
            f"[Source: {chunk['source']}]\n{chunk['content']}"
        )

    return "\n\n---\n\n".join(parts)
