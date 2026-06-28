"""
Tests for Issue #4: Scrape + keyword filter + SSE pipeline shell.

1. filter_jobs includes jobs that match keywords_include
2. filter_jobs excludes jobs that match keywords_exclude
3. filter_jobs with empty keyword lists lets everything through
4. POST /run returns text/event-stream content type (jobspy mocked)
5. POST /run emits run_failed when persona.json is missing
"""
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_job(title: str, description: str) -> dict:
    return {"title": title, "description": description, "company": "ACME", "location": "Paris"}


def parse_sse_events(text: str) -> list[dict]:
    """Parse the raw SSE body into a list of JSON payloads."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload = line[len("data:"):].strip()
            if payload:
                events.append(json.loads(payload))
    return events


# ---------------------------------------------------------------------------
# filter_jobs tests (pure function — no I/O)
# ---------------------------------------------------------------------------

class TestFilterJobs:
    def test_includes_jobs_matching_keywords_include(self):
        from main import filter_jobs

        jobs = [
            make_job("Python Developer", "Build APIs with FastAPI"),
            make_job("Sales Manager", "Grow revenue"),
        ]
        config = {"keywords_include": ["python"], "keywords_exclude": []}
        result = filter_jobs(jobs, config)
        assert len(result) == 1
        assert result[0]["title"] == "Python Developer"

    def test_excludes_jobs_matching_keywords_exclude(self):
        from main import filter_jobs

        jobs = [
            make_job("Backend Engineer", "Python microservices"),
            make_job("Junior Backend Engineer", "Python junior position"),
        ]
        config = {"keywords_include": [], "keywords_exclude": ["junior"]}
        result = filter_jobs(jobs, config)
        assert len(result) == 1
        assert result[0]["title"] == "Backend Engineer"

    def test_empty_keyword_lists_passes_all_jobs(self):
        from main import filter_jobs

        jobs = [
            make_job("Any Title", "Any description"),
            make_job("Another Job", "Totally different"),
        ]
        config = {"keywords_include": [], "keywords_exclude": []}
        result = filter_jobs(jobs, config)
        assert len(result) == 2

    def test_case_insensitive_include(self):
        from main import filter_jobs

        jobs = [make_job("PYTHON DEVELOPER", "FASTAPI")]
        config = {"keywords_include": ["python"], "keywords_exclude": []}
        result = filter_jobs(jobs, config)
        assert len(result) == 1

    def test_case_insensitive_exclude(self):
        from main import filter_jobs

        jobs = [make_job("Sales Manager", "Manage SALES team")]
        config = {"keywords_include": [], "keywords_exclude": ["SALES"]}
        result = filter_jobs(jobs, config)
        assert len(result) == 0

    def test_all_excluded_returns_empty(self):
        from main import filter_jobs

        jobs = [make_job("Sales Rep", "Door-to-door sales"), make_job("Senior Sales", "Sales leadership")]
        config = {"keywords_include": [], "keywords_exclude": ["sales"]}
        result = filter_jobs(jobs, config)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# POST /run endpoint tests (jobspy mocked)
# ---------------------------------------------------------------------------

def _make_fake_df(jobs: list[dict] | None = None) -> pd.DataFrame:
    """Return a minimal DataFrame that mimics jobspy output."""
    if jobs is None:
        jobs = [
            {
                "title": "Python Developer",
                "company": "ACME",
                "location": "Paris",
                "description": "FastAPI experience required",
                "job_url": "https://example.com/1",
                "min_amount": None,
            }
        ]
    return pd.DataFrame(jobs)


@pytest.fixture()
def client_with_all_files(tmp_path, monkeypatch):
    """
    TestClient where all required files exist and paths are patched to tmp_path.
    Also patches SEARCH_CONFIG_PATH to avoid reading real disk config.
    """
    import main as m

    # Create required files
    (tmp_path / "persona.json").write_text(json.dumps({"name": "Test User"}))
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "base_cv.txt").write_text("My CV")
    (tmp_path / "input" / "base_cover_letter.txt").write_text("My cover letter")

    monkeypatch.setattr(m, "PERSONA_PATH", str(tmp_path / "persona.json"))
    monkeypatch.setattr(m, "BASE_CV_PATH", str(tmp_path / "input" / "base_cv.txt"))
    monkeypatch.setattr(m, "BASE_COVER_LETTER_PATH", str(tmp_path / "input" / "base_cover_letter.txt"))

    # Use an in-memory-ish temp db
    db_path = str(tmp_path / "test.db")
    import database
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    # No search_config.json — will use defaults
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", str(tmp_path / "nonexistent_search_config.json"))

    return TestClient(m.app)


@pytest.fixture()
def client_missing_persona(tmp_path, monkeypatch):
    """TestClient where persona.json is absent."""
    import main as m

    monkeypatch.setattr(m, "PERSONA_PATH", str(tmp_path / "persona.json"))  # does not exist
    monkeypatch.setattr(m, "BASE_CV_PATH", str(tmp_path / "base_cv.txt"))
    monkeypatch.setattr(m, "BASE_COVER_LETTER_PATH", str(tmp_path / "base_cover_letter.txt"))

    return TestClient(m.app)


def test_post_run_returns_text_event_stream(client_with_all_files):
    with patch("main.scrape_jobs", return_value=_make_fake_df()):
        response = client_with_all_files.post("/run")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


def test_post_run_emits_expected_sse_events(client_with_all_files):
    with patch("main.scrape_jobs", return_value=_make_fake_df()):
        response = client_with_all_files.post("/run")

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "run_started" in event_names
    assert "scraping_started" in event_names
    assert "scraping_complete" in event_names
    assert "filtering_complete" in event_names
    assert "run_complete" in event_names


def test_post_run_emits_run_failed_when_persona_missing(client_missing_persona):
    response = client_missing_persona.post("/run")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "run_failed" in event_names
    # Should NOT have proceeded to scraping
    assert "run_started" not in event_names


def test_post_run_scraping_complete_event_has_count(client_with_all_files):
    fake_df = _make_fake_df([
        {"title": "Dev", "company": "A", "location": "Paris",
         "description": "Python", "job_url": "https://x.com/1", "min_amount": None},
        {"title": "Engineer", "company": "B", "location": "Lyon",
         "description": "Django", "job_url": "https://x.com/2", "min_amount": None},
    ])
    client = client_with_all_files
    with patch("main.scrape_jobs", return_value=fake_df):
        response = client.post("/run")

    events = parse_sse_events(response.text)
    scraping_complete = next(e for e in events if e["event"] == "scraping_complete")
    assert scraping_complete["count"] == 2
