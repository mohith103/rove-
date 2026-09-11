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
        # Local development
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        # Local network (for iOS / tablet testing)
        # Replace 192.168.1.42 with YOUR Mac's IP
        "http://192.168.1.42:5173",
        "http://192.168.1.42:8000",
    ])
    # How often to broadcast state over WebSocket (seconds)
    stream_interval: float = 0.5
    # How many simulation steps to advance per stream interval
    stream_steps_per_tick: int = 1


# Singleton — imported by main.py
settings = BackendConfig()