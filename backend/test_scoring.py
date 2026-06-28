"""
Tests for Issue #5: LLM integration + job scoring.

1. test_score_job_returns_valid_structure
   — mock call_llm to return valid JSON, assert score is int and reasoning is str
2. test_score_job_handles_invalid_llm_response
   — mock call_llm to return garbage, assert graceful fallback (score=0)
3. test_post_run_emits_scoring_events
   — mock scrape_jobs AND score_job, assert scoring_job and scoring_complete
     events appear in the SSE stream
4. test_top_n_jobs_selected
   — mock scoring to return known scores, assert only top N are marked selected
"""
import json
import sqlite3
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def make_fake_df(jobs: list[dict] | None = None) -> pd.DataFrame:
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
    """
    import main as m

    # Create required files
    persona = {"skills": ["Python"], "experience_years": 5, "target_titles": ["Developer"]}
    (tmp_path / "persona.json").write_text(json.dumps(persona))
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

    # No search_config.json — will use defaults (max_jobs=5)
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", str(tmp_path / "nonexistent_search_config.json"))

    return TestClient(m.app), db_path


# ---------------------------------------------------------------------------
# 1. score_job returns valid structure
# ---------------------------------------------------------------------------

def test_score_job_returns_valid_structure():
    from agents import score_job

    valid_response = json.dumps({"score": 8, "reasoning": "Strong Python and FastAPI match."})
    with patch("agents.call_llm", return_value=valid_response):
        result = score_job(
            persona={"skills": ["Python"], "experience_years": 3},
            job={"title": "Python Developer", "description": "Build APIs with FastAPI"},
        )

    assert isinstance(result["score"], int)
    assert isinstance(result["reasoning"], str)
    assert result["score"] == 8
    assert result["reasoning"] == "Strong Python and FastAPI match."


# ---------------------------------------------------------------------------
# 2. score_job handles invalid LLM response gracefully
# ---------------------------------------------------------------------------

def test_score_job_handles_invalid_llm_response():
    from agents import score_job

    with patch("agents.call_llm", return_value="this is not json at all!!!"):
        result = score_job(
            persona={"skills": ["Python"]},
            job={"title": "Any Job", "description": "Any description"},
        )

    assert result["score"] == 0
    assert "Failed to parse" in result["reasoning"]


# ---------------------------------------------------------------------------
# 3. POST /run emits scoring_job and scoring_complete events
# ---------------------------------------------------------------------------

def test_post_run_emits_scoring_events(client_with_all_files):
    client, db_path = client_with_all_files

    fake_score = {"score": 7, "reasoning": "Good fit."}
    with patch("main.scrape_jobs", return_value=make_fake_df()):
        with patch("main.score_job", return_value=fake_score):
            response = client.post("/run")

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "scoring_job" in event_names, f"scoring_job not found in {event_names}"
    assert "scoring_complete" in event_names, f"scoring_complete not found in {event_names}"
    assert "run_complete" in event_names

    # Verify scoring_job event has title and score fields
    scoring_job_event = next(e for e in events if e["event"] == "scoring_job")
    assert "title" in scoring_job_event
    assert "score" in scoring_job_event

    # Verify scoring_complete event has a count
    scoring_complete_event = next(e for e in events if e["event"] == "scoring_complete")
    assert "count" in scoring_complete_event


# ---------------------------------------------------------------------------
# 4. Top N jobs are selected in SQLite
# ---------------------------------------------------------------------------

def test_top_n_jobs_selected(tmp_path, monkeypatch):
    """
    Provide 5 jobs with known scores, set max_jobs=3, verify only top 3 are selected.
    """
    import main as m
    import database

    persona = {"skills": ["Python"], "experience_years": 5}
    (tmp_path / "persona.json").write_text(json.dumps(persona))
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "base_cv.txt").write_text("My CV")
    (tmp_path / "input" / "base_cover_letter.txt").write_text("My cover letter")

    monkeypatch.setattr(m, "PERSONA_PATH", str(tmp_path / "persona.json"))
    monkeypatch.setattr(m, "BASE_CV_PATH", str(tmp_path / "input" / "base_cv.txt"))
    monkeypatch.setattr(m, "BASE_COVER_LETTER_PATH", str(tmp_path / "input" / "base_cover_letter.txt"))

    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    # Use a search config with max_jobs=3
    search_config = {
        "target_titles": ["Developer"],
        "location": "",
        "country": "",
        "language": "en",
        "keywords_include": [],
        "keywords_exclude": [],
        "max_jobs": 3,
    }
    config_path = str(tmp_path / "search_config.json")
    (tmp_path / "search_config.json").write_text(json.dumps(search_config))
    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", config_path)

    # 5 jobs with predictable titles
    jobs_data = [
        {"title": f"Job {i}", "company": "Co", "location": "Paris",
         "description": "Python work", "job_url": f"https://x.com/{i}", "min_amount": None}
        for i in range(1, 6)
    ]
    fake_df = pd.DataFrame(jobs_data)

    # Scores: Job 1→9, Job 2→3, Job 3→7, Job 4→5, Job 5→8
    score_map = {
        "Job 1": {"score": 9, "reasoning": "Top fit."},
        "Job 2": {"score": 3, "reasoning": "Poor fit."},
        "Job 3": {"score": 7, "reasoning": "Good fit."},
        "Job 4": {"score": 5, "reasoning": "Average fit."},
        "Job 5": {"score": 8, "reasoning": "Strong fit."},
    }

    def fake_score_job(persona, job):
        return score_map.get(job["title"], {"score": 0, "reasoning": "Unknown"})

    client = TestClient(m.app)
    with patch("main.scrape_jobs", return_value=fake_df):
        with patch("main.score_job", side_effect=fake_score_job):
            response = client.post("/run")

    assert response.status_code == 200

    # Check SQLite — only top 3 by score should be selected
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, score, selected FROM jobs ORDER BY score DESC")
    rows = cursor.fetchall()
    conn.close()

    selected_titles = {title for title, score, selected in rows if selected == 1}
    # Top 3 scores: Job 1 (9), Job 5 (8), Job 3 (7)
    assert selected_titles == {"Job 1", "Job 5", "Job 3"}, (
        f"Expected top-3 selected, got: {selected_titles}"
    )
    # Non-top jobs should NOT be selected
    unselected_titles = {title for title, score, selected in rows if selected == 0}
    assert "Job 2" in unselected_titles
    assert "Job 4" in unselected_titles
