"""WebSocket streaming for missions."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.api.missions import get_service
from backend.app.config import settings

router = APIRouter(tags=["stream"])


@router.websocket("/missions/{mission_id}/stream")
async def stream_mission(websocket: WebSocket, mission_id: str) -> None:
    await websocket.accept()
    service = get_service()
    mission = service.get(mission_id)
    if mission is None:
        await websocket.send_json({"error": "mission not found"})
        await websocket.close()
        return

    try:
        while True:
            payload = {
                "summary": mission.to_summary(),
                "state": mission.world_state(),
                "last_decision": mission.decisions[-1] if mission.decisions else None,
            }
            await websocket.send_text(json.dumps(payload, default=str))
            if mission.status == "done":
                await websocket.send_json({"status": "done"})
                break
            await asyncio.sleep(settings.stream_interval)
    except WebSocketDisconnect:
        return
    finally:
        try:
            await websocket.close()
        except Exception:
            pass