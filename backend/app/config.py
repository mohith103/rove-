"""Backend settings for the ROVE API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    """Config for the FastAPI app.

    Kept minimal — simulation parameters come from `configs/default.yaml`.
    """
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA fallback
        "http://127.0.0.1:5173",
    ])
    # How often to broadcast state over WebSocket (seconds)
    stream_interval: float = 0.5
    # How many simulation steps to advance per stream interval
    stream_steps_per_tick: int = 1


# Singleton — imported by main.py
settings = BackendConfig()