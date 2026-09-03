"""
RAG ingestion pipeline:
  1. Load markdown documents from the knowledge base directory
  2. Split into overlapping chunks
  3. Embed with sentence-transformers
  4. Store in ChromaDB
"""
import logging
import os
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)
settings = get_settings()

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"
CHUNK_SIZE = 512      # characters per chunk
CHUNK_OVERLAP = 64    # overlap between consecutive chunks


def _get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path=settings.vector_db_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping fixed-size chunks, preserving paragraph boundaries where possible."""
    # Prefer splitting on paragraph boundaries
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If single paragraph is larger than chunk_size, split it
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i : i + chunk_size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def ingest_knowledge_base(force_reingest: bool = False) -> int:
    """
    Ingest all markdown files from the knowledge base directory into ChromaDB.
    Returns the total number of chunks stored.
    Skips if already ingested unless force_reingest=True.
    """
    client = _get_chroma_client()

    # Check if collection already exists and has data
    try:
        collection = client.get_collection(settings.vector_db_collection)
        if collection.count() > 0 and not force_reingest:
            logger.info(f"Knowledge base already ingested ({collection.count()} chunks). Skipping.")
            return collection.count()
        # Delete and recreate for reingest
        client.delete_collection(settings.vector_db_collection)
    except Exception:
        pass

    collection = client.create_collection(
        name=settings.vector_db_collection,
        metadata={"hnsw:space": "cosine"},
    )

    if not KNOWLEDGE_BASE_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return 0

    doc_files = list(KNOWLEDGE_BASE_DIR.glob("*.md"))
    if not doc_files:
        logger.warning("No markdown files found in knowledge base directory.")
        return 0

    all_chunks = []
    all_metadata = []
    all_ids = []

    for doc_path in doc_files:
        try:
            text = doc_path.read_text(encoding="utf-8")
            source_name = doc_path.stem.replace("_", " ").title()
            chunks = _split_text(text)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_path.stem}_{i}"
                all_ids.append(chunk_id)
                all_chunks.append(chunk)
                all_metadata.append({
                    "source": source_name,
                    "file": doc_path.name,
                    "chunk_index": i,
                })

            logger.info(f"Processed '{doc_path.name}' → {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to process {doc_path.name}: {e}")

    if not all_chunks:
        return 0

    # Embed in batches of 64
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        embeddings = embed_texts(batch)
        all_embeddings.extend(embeddings)
        logger.info(f"Embedded chunks {i}–{i + len(batch)}")

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=all_embeddings,
        metadatas=all_metadata,
    )

    logger.info(f"Knowledge base ingested: {len(all_chunks)} total chunks.")
    return len(all_chunks)
