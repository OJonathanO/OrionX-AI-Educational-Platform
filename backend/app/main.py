"""FastAPI application entry point for the AI Educational Platform."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import (
    auth,
    users,
    documents,
    chat,
    conversations,
    quizzes,
    recommendations,
    analytics,
    admin,
    health,
)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations.router, prefix=settings.API_V1_PREFIX)
app.include_router(quizzes.router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router)  # Health at /api/health


@app.on_event("startup")
def startup():
    """Initialize the database on application startup."""
    init_db()


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {"message": "AI Educational Platform API", "version": "1.0.0", "docs": "/docs"}
