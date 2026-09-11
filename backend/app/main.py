"""ROVE FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import analysis, counterfactual, experiments, missions, models
from backend.app.config import settings
from backend.app.websocket import stream


def create_app() -> FastAPI:
    app = FastAPI(
        title="ROVE API",
        description="Autonomous rover mission simulation.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(missions.router)
    app.include_router(models.router)
    app.include_router(experiments.router)
    app.include_router(counterfactual.router)
    app.include_router(analysis.router)
    app.include_router(stream.router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
