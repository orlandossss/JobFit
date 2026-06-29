"""
Tests for Issue #2: Persona endpoint.
- GET /persona returns 200 with JSON content when persona.json exists
- GET /persona returns 404 when persona.json is missing
"""
import json
import os
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def persona_file(tmp_path, monkeypatch):
    """Create a temporary persona.json and point the app at it."""
    data = {
        "name": "Jane Doe",
        "skills": ["Python", "FastAPI"],
        "experience_years": 5,
        "target_roles": ["Backend Engineer"],
    }
    persona_path = tmp_path / "persona.json"
    persona_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("PERSONA_PATH", str(persona_path))
    return str(persona_path), data


@pytest.fixture()
def no_persona_file(tmp_path, monkeypatch):
    """Point the app at a path where persona.json does not exist."""
    missing_path = tmp_path / "persona.json"
    monkeypatch.setenv("PERSONA_PATH", str(missing_path))


def test_get_persona_returns_200_with_content(persona_file):
    """GET /persona returns 200 and the parsed JSON when persona.json exists."""
    from main import app

    _, expected_data = persona_file
    client = TestClient(app)
    response = client.get("/persona")
    assert response.status_code == 200
    assert response.json() == expected_data


def test_get_persona_returns_404_when_missing(no_persona_file):
    """GET /persona returns 404 with a helpful message when persona.json is absent."""
    from main import app

    client = TestClient(app)
    response = client.get("/persona")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    # Message should hint at how to create the persona
    assert "build-persona" in body["detail"].lower() or "skill" in body["detail"].lower()
