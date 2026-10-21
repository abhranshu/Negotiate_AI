"""Shared pytest fixtures for the NegotiateAI test suite.

Important: the environment is configured BEFORE ``api.main`` is imported, so the
app under test uses an isolated SQLite database and does not try to load the
heavy local LLM / ASR models. That keeps the suite fast and deterministic while
still exercising the real FastAPI routes and DB layer.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Test environment (set before importing the app) ──────────────────────────
_TEST_DB = ROOT / "test_negotiateai.db"
_TEST_UPLOADS = ROOT / "test_uploads"

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["USE_LOCAL_MODEL"] = "false"
os.environ["USE_LOCAL_ASR"] = "false"
os.environ["USE_EXTERNAL_LLM"] = "false"
os.environ["ALLOWED_ORIGINS"] = '["*"]'
os.environ["UPLOAD_DIR"] = _TEST_UPLOADS.as_posix()

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Session-scoped FastAPI TestClient (runs app lifespan, i.e. migrations)."""
    from fastapi.testclient import TestClient

    from api.main import app

    _TEST_UPLOADS.mkdir(exist_ok=True)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    """Register + login a fresh claimant and return Authorization headers."""
    import uuid

    email = f"claimant_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Test Claimant", "password": "TestPass@123"},
    )
    assert r.status_code == 201, r.text
    r = client.post(
        "/api/auth/login", data={"username": email, "password": "TestPass@123"}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
