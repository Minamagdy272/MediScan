"""
FastAPI Health Check Endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check():
    """Returns system status, active models, and readiness."""
    from pipeline.config import (
        ROUTER_MODEL,
        AGENT_MODEL,
        EVALUATOR_MODEL,
        EMBEDDING_MODEL,
        RERANKER_MODEL
    )

    return {
        "status": "healthy",
        "service": "MediScan Clinical AI Assistant",
        "models": {
            "router": ROUTER_MODEL,
            "planner": AGENT_MODEL,
            "generator": AGENT_MODEL,
            "evaluator": EVALUATOR_MODEL,
            "embeddings": EMBEDDING_MODEL,
            "reranker": RERANKER_MODEL
        }
    }
