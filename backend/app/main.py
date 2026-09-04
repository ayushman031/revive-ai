"""FastAPI application entry point for the REVIVE API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Create the REVIVE API without establishing external service connections.

    External connections (database, Redis) are established lazily on first use
    so the application factory remains fast and side-effect-free for testing.
    """
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI Revenue Recovery Agent — Razorpay Buildathon Track 03",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    return application


app = create_app()
