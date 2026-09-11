"""API tests using FastAPI's TestClient (synchronous, no server needed)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_health():
    with _client() as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_list_models():
    with _client() as c:
        r = c.get("/models")
        assert r.status_code == 200
        data = r.json()
        assert "agents" in data
        names = [a["name"] for a in data["agents"]]
        assert "rule_based" in names


def test_create_and_get_mission():
    with _client() as c:
        r = c.post("/missions", json={
            "difficulty": "medium",
            "agent": "rule_based",
            "mode": "balanced",
            "seed": 42,
            "speed": 5.0,
        })
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["agent"] == "rule_based"
        assert m["status"] in ("running", "done")

        # Read it back
        r2 = c.get(f"/missions/{m['id']}")
        assert r2.status_code == 200
        detail = r2.json()
        assert detail["id"] == m["id"]
        assert "state" in detail


def test_mission_not_found():
    with _client() as c:
        r = c.get("/missions/does-not-exist")
        assert r.status_code == 404


def test_pause_and_resume():
    with _client() as c:
        r = c.post("/missions", json={
            "difficulty": "easy",
            "agent": "rule_based",
            "mode": "balanced",
            "seed": 1,
            "speed": 1.0,
        })
        mid = r.json()["id"]
        p = c.post(f"/missions/{mid}/pause")
        assert p.status_code == 200
        assert p.json()["status"] == "paused"
        r2 = c.post(f"/missions/{mid}/resume")
        assert r2.status_code == 200


def test_manual_action():
    with _client() as c:
        r = c.post("/missions", json={
            "difficulty": "easy",
            "agent": "rule_based",
            "mode": "balanced",
            "seed": 2,
            "speed": 1.0,
        })
        mid = r.json()["id"]
        a = c.post(f"/missions/{mid}/action", json={"action": 10})  # WAIT
        assert a.status_code == 200