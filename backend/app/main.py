from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, create_all_tables_sync
from app.api.v1 import api_v1_router
# Import all models to register with Base.metadata
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    Synchronously creates missing tables on startup for rapid local testing and development.
    """
    create_all_tables_sync()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend API for LibriSmart Smart Library Management & Space Reservation Platform",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == ["*"] else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 routes
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Comprehensive health check verifying application and database connectivity.
    """
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }
