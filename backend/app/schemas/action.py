"""Action-related schemas."""
from __future__ import annotations

from pydantic import BaseModel


class ActionInfo(BaseModel):
    id: int
    name: str


class ActionListResponse(BaseModel):
    actions: list[ActionInfo]