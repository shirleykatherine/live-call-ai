"""
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db

logger = logging.getLogger(__name__)
settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown tasks."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database and seed demo data
    logger.info("Initializing database...")
    init_db()

    # Ingest knowledge base into ChromaDB
    logger.info("Ingesting knowledge base...")
    try:
        from app.rag.ingestion import ingest_knowledge_base
        chunks = ingest_knowledge_base()
        logger.info(f"Knowledge base ready: {chunks} chunks.")
    except Exception as e:
        logger.error(f"Knowledge base ingestion failed: {e}")

    # Pre-load embedding model to avoid first-request latency
    logger.info("Pre-loading embedding model...")
    try:
        from app.rag.embeddings import get_embedding_model
        get_embedding_model()
    except Exception as e:
        logger.error(f"Embedding model pre-load failed: {e}")

    # Pre-compile the LangGraph
    logger.info("Compiling LangGraph agent...")
    try:
        from app.agents.graph import get_compiled_graph
        get_compiled_graph()
    except Exception as e:
        logger.error(f"LangGraph compilation failed: {e}")

    logger.info("All systems ready.")
    yield

    logger.info("Shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered real-time call co-pilot for customer service agents.",
    lifespan=lifespan,
)

# CORS — allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
from app.api.calls import router as calls_router
from app.api.transcripts import router as transcripts_router
from app.api.evaluation import router as evaluation_router

app.include_router(calls_router)
app.include_router(transcripts_router)
app.include_router(evaluation_router)


# WebSocket endpoint
@app.websocket("/ws/{call_id}")
async def websocket_endpoint(websocket: WebSocket, call_id: str):
    from app.websocket.handler import handle_websocket
    await handle_websocket(websocket, call_id)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
