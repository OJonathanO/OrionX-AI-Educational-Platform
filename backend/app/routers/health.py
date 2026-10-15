"""Health check and service status router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.rag.vector_store import get_vector_store
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check(db: Session = Depends(get_db)):
    """Check the status of all platform services.

    Returns the health of the database, vector store, embedding provider,
    and LLM provider.
    """
    services = {}

    # Database health
    try:
        db.execute(text("SELECT 1"))
        services["database"] = {"status": "healthy", "detail": "Connected"}
    except Exception as e:
        services["database"] = {"status": "unhealthy", "detail": str(e)}

    # Vector store health
    try:
        vector_store = get_vector_store()
        count = vector_store.count()
        services["vector_store"] = {
            "status": "healthy",
            "detail": f"Operational ({count} chunks stored)",
        }
    except Exception as e:
        services["vector_store"] = {"status": "unhealthy", "detail": str(e)}

    # Embedding provider health
    try:
        provider_name = settings.EMBEDDING_PROVIDER
        model_name = settings.EMBEDDING_MODEL
        services["embedding_provider"] = {
            "status": "healthy",
            "detail": f"{provider_name} ({model_name}) configured",
        }
    except Exception as e:
        services["embedding_provider"] = {"status": "unhealthy", "detail": str(e)}

    # LLM provider health
    try:
        from app.rag.generation import get_generation_service
        generation = get_generation_service()
        services["llm_provider"] = {
            "status": "healthy",
            "detail": f"{settings.LLM_PROVIDER} ({settings.LLM_MODEL}) configured",
        }
    except Exception as e:
        services["llm_provider"] = {"status": "unhealthy", "detail": str(e)}

    # Overall status
    all_healthy = all(s["status"] == "healthy" for s in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
    }


@router.get("/ready")
def readiness_probe():
    """Simple readiness probe for container orchestration."""
    return {"ready": True}
