"""
Tests for Issue #6: Document generation + results page.

1. test_rewrite_cv_returns_string
   — mock call_llm, assert return is non-empty string
2. test_write_cover_letter_returns_string
   — mock call_llm, assert return is non-empty string
3. test_post_run_emits_generating_events
   — mock scrape_jobs, score_job, rewrite_cv, write_cover_letter;
     assert generating_cv, generating_cover_letter, run_complete events in SSE stream
4. test_output_files_created
   — mock everything, assert .txt files are written to the correct output/YYYY-MM-DD/ path
5. test_get_runs_returns_list
   — seed SQLite with a run record, assert endpoint returns it
6. test_get_run_results_returns_selected_jobs
   — seed SQLite with run + selected jobs, assert correct data returned
"""
import json
import os
import sqlite3
from datetime import datetime
from unittest.mock import patch

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
                "company": "ACME Corp",
                "location": "Paris",
                "description": "FastAPI experience required",
                "job_url": "https://example.com/1",
                "min_amount": None,
            }
        ]
    return pd.DataFrame(jobs)


@pytest.fixture()
def full_client(tmp_path, monkeypatch):
    """
    TestClient with all required files, temp DB, and temp output dir.
    Returns (client, db_path, tmp_path).
    """
    import main as m
    import database

    persona = {"skills": ["Python"], "experience_years": 5, "target_titles": ["Developer"]}
    (tmp_path / "persona.json").write_text(json.dumps(persona))
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "base_cv.txt").write_text("My base CV content")
    (tmp_path / "input" / "base_cover_letter.txt").write_text("My base cover letter")

    monkeypatch.setattr(m, "PERSONA_PATH", str(tmp_path / "persona.json"))
    monkeypatch.setattr(m, "BASE_CV_PATH", str(tmp_path / "input" / "base_cv.txt"))
    monkeypatch.setattr(m, "BASE_COVER_LETTER_PATH", str(tmp_path / "input" / "base_cover_letter.txt"))
    monkeypatch.setattr(m, "OUTPUT_DIR", str(tmp_path / "output"))

    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    monkeypatch.setattr(m, "SEARCH_CONFIG_PATH", str(tmp_path / "nonexistent_search_config.json"))

    return TestClient(m.app), db_path, tmp_path


# ---------------------------------------------------------------------------
# 1. rewrite_cv returns a non-empty string
# ---------------------------------------------------------------------------

def test_rewrite_cv_returns_string():
    from agents import rewrite_cv

    with patch("agents.call_llm", return_value="Tailored CV text here."):
        result = rewrite_cv(
            persona={"skills": ["Python"], "experience_years": 3},
            base_cv="Original CV content",
            job={"title": "Python Developer", "company": "ACME", "description": "Build APIs"},
        )

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "Tailored CV text here."


# ---------------------------------------------------------------------------
# 2. write_cover_letter returns a non-empty string
# ---------------------------------------------------------------------------

def test_write_cover_letter_returns_string():
    from agents import write_cover_letter

    with patch("agents.call_llm", return_value="Dear Hiring Manager, ..."):
        result = write_cover_letter(
            persona={"skills": ["Python"], "experience_years": 3},
            base_cover_letter="Original cover letter",
            job={"title": "Python Developer", "company": "ACME", "description": "Build APIs"},
        )

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "Dear Hiring Manager, ..."


# ---------------------------------------------------------------------------
# 3. POST /run emits generating_cv, generating_cover_letter, run_complete events
# ---------------------------------------------------------------------------

def test_post_run_emits_generating_events(full_client):
    client, db_path, tmp_path = full_client

    fake_score = {"score": 8, "reasoning": "Strong fit."}

    with patch("main.scrape_jobs", return_value=make_fake_df()):
        with patch("main.score_job", return_value=fake_score):
            with patch("main.rewrite_cv", return_value="Tailored CV"):
                with patch("main.write_cover_letter", return_value="Tailored Cover Letter"):
                    response = client.post("/run")

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "generating_cv" in event_names, f"generating_cv not found in {event_names}"
    assert "generating_cover_letter" in event_names, f"generating_cover_letter not found in {event_names}"
    assert "run_complete" in event_names, f"run_complete not found in {event_names}"

    # Verify generating_cv event has company and title fields
    gen_cv_event = next(e for e in events if e["event"] == "generating_cv")
    assert "company" in gen_cv_event
    assert "title" in gen_cv_event

    # Verify generating_cover_letter event has company and title fields
    gen_cl_event = next(e for e in events if e["event"] == "generating_cover_letter")
    assert "company" in gen_cl_event
    assert "title" in gen_cl_event

    # Verify run_complete has run_id
    run_complete_event = next(e for e in events if e["event"] == "run_complete")
    assert "run_id" in run_complete_event


# ---------------------------------------------------------------------------
# 4. Output .txt files are written to output/YYYY-MM-DD/
# ---------------------------------------------------------------------------

def test_output_files_created(full_client):
    client, db_path, tmp_path = full_client
    output_dir = tmp_path / "output"

    fake_score = {"score": 8, "reasoning": "Strong fit."}

    with patch("main.scrape_jobs", return_value=make_fake_df()):
        with patch("main.score_job", return_value=fake_score):
            with patch("main.rewrite_cv", return_value="My tailored CV"):
                with patch("main.write_cover_letter", return_value="My tailored cover letter"):
                    response = client.post("/run")

    assert response.status_code == 200

    # Output directory should contain a dated subfolder
    today = datetime.now().strftime("%Y-%m-%d")
    dated_dir = output_dir / today
    assert dated_dir.exists(), f"Expected output folder {dated_dir} to exist"

    # Should contain CV and cover letter files
    txt_files = list(dated_dir.glob("*.txt"))
    assert len(txt_files) == 2, f"Expected 2 .txt files, found: {[f.name for f in txt_files]}"

    cv_files = [f for f in txt_files if f.name.endswith("_cv.txt")]
    cl_files = [f for f in txt_files if f.name.endswith("_cover_letter.txt")]

    assert len(cv_files) == 1, "Expected one _cv.txt file"
    assert len(cl_files) == 1, "Expected one _cover_letter.txt file"

    # Verify content was written
    assert cv_files[0].read_text() == "My tailored CV"
    assert cl_files[0].read_text() == "My tailored cover letter"


# ---------------------------------------------------------------------------
# 5. GET /runs returns list of run records
# ---------------------------------------------------------------------------

def test_get_runs_returns_list(tmp_path, monkeypatch):
    import main as m
    import database

    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    # Seed a run record
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-06-28T10:00:00+00:00", 10, 7, 3, "complete"),
    )
    conn.commit()
    conn.close()

    client = TestClient(m.app)
    response = client.get("/runs")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    run = data[0]
    assert run["jobs_found"] == 10
    assert run["jobs_after_filter"] == 7
    assert run["jobs_selected"] == 3
    assert run["status"] == "complete"


# ---------------------------------------------------------------------------
# 6. GET /runs/{run_id}/results returns selected jobs
# ---------------------------------------------------------------------------

def test_get_run_results_returns_selected_jobs(tmp_path, monkeypatch):
    import main as m
    import database

    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    # Seed a run + selected and unselected jobs
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-06-28T10:00:00+00:00", 5, 3, 2, "complete"),
    )
    run_id = cursor.lastrowid

    # Insert 2 selected jobs
    cursor.execute(
        """INSERT INTO jobs (run_id, title, company, location, score, reasoning, selected, cv_path, cover_letter_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, "Python Developer", "ACME", "Paris", 9.0, "Top fit.", 1, "/path/cv1.txt", "/path/cl1.txt"),
    )
    cursor.execute(
        """INSERT INTO jobs (run_id, title, company, location, score, reasoning, selected, cv_path, cover_letter_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, "Backend Engineer", "Beta Corp", "Lyon", 7.0, "Good fit.", 1, "/path/cv2.txt", "/path/cl2.txt"),
    )
    # Insert 1 unselected job
    cursor.execute(
        """INSERT INTO jobs (run_id, title, company, location, score, reasoning, selected)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, "Sales Manager", "Gamma", "Bordeaux", 2.0, "Poor fit.", 0),
    )
    conn.commit()
    conn.close()

    client = TestClient(m.app)
    response = client.get(f"/runs/{run_id}/results")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2, f"Expected 2 selected jobs, got {len(data)}"

    titles = {job["title"] for job in data}
    assert "Python Developer" in titles
    assert "Backend Engineer" in titles
    assert "Sales Manager" not in titles

    # Verify fields are present
    for job in data:
        assert "score" in job
        assert "reasoning" in job
        assert "cv_path" in job
        assert "cover_letter_path" in job
