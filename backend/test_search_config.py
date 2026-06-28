"""
Tests for Issue #3: Search config endpoints.
- GET /search-config returns defaults when file missing
- GET /search-config returns file contents when file exists
- PUT /search-config writes to disk and returns saved config
- PUT /search-config with invalid data returns 422
"""
import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


DEFAULTS = {
    "target_titles": [],
    "location": "",
    "country": "",
    "language": "en",
    "keywords_include": [],
    "keywords_exclude": [],
    "max_jobs": 5,
}

VALID_CONFIG = {
    "target_titles": ["Software Engineer", "Backend Developer"],
    "location": "Paris, France",
    "country": "France",
    "language": "en",
    "keywords_include": ["Python", "API"],
    "keywords_exclude": ["sales", "junior"],
    "max_jobs": 10,
}


@pytest.fixture()
def client_no_config(tmp_path, monkeypatch):
    """TestClient with no search_config.json on disk."""
    import main as m
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", str(tmp_path / "search_config.json"))
    return TestClient(m.app)


@pytest.fixture()
def client_with_config(tmp_path, monkeypatch):
    """TestClient with a pre-existing search_config.json on disk."""
    config_path = tmp_path / "search_config.json"
    config_path.write_text(json.dumps(VALID_CONFIG))
    import main as m
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", str(config_path))
    return TestClient(m.app), str(config_path)


def test_get_search_config_returns_defaults_when_file_missing(client_no_config):
    response = client_no_config.get("/search-config")
    assert response.status_code == 200
    data = response.json()
    assert data["target_titles"] == []
    assert data["location"] == ""
    assert data["country"] == ""
    assert data["language"] == "en"
    assert data["keywords_include"] == []
    assert data["keywords_exclude"] == []
    assert data["max_jobs"] == 5


def test_get_search_config_returns_file_contents_when_file_exists(client_with_config):
    client, _ = client_with_config
    response = client.get("/search-config")
    assert response.status_code == 200
    data = response.json()
    assert data["target_titles"] == ["Software Engineer", "Backend Developer"]
    assert data["location"] == "Paris, France"
    assert data["country"] == "France"
    assert data["language"] == "en"
    assert data["keywords_include"] == ["Python", "API"]
    assert data["keywords_exclude"] == ["sales", "junior"]
    assert data["max_jobs"] == 10


def test_put_search_config_writes_to_disk_and_returns_saved_config(client_no_config, tmp_path, monkeypatch):
    import main as m
    config_path = str(tmp_path / "search_config.json")
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", config_path)
    client = TestClient(m.app)

    response = client.put("/search-config", json=VALID_CONFIG)
    assert response.status_code == 200
    returned = response.json()
    assert returned["target_titles"] == VALID_CONFIG["target_titles"]
    assert returned["max_jobs"] == VALID_CONFIG["max_jobs"]

    # Verify file was actually written to disk
    assert os.path.exists(config_path)
    with open(config_path) as f:
        on_disk = json.load(f)
    assert on_disk["location"] == "Paris, France"
    assert on_disk["language"] == "en"


def test_put_search_config_with_invalid_data_returns_422(client_no_config):
    # max_jobs must be an int — send a string to trigger validation failure
    response = client_no_config.put(
        "/search-config",
        json={
            "target_titles": ["Engineer"],
            "location": "Paris",
            "country": "France",
            "language": "en",
            "keywords_include": [],
            "keywords_exclude": [],
            "max_jobs": "not-a-number",
        },
    )
    assert response.status_code == 422
