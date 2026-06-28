"""
Tests for Issue #7: History page backend behaviour.

1. test_get_runs_returns_empty_list_when_no_runs
   — fresh DB, assert GET /runs returns []
2. test_get_runs_returns_runs_newest_first
   — seed two runs with different dates, assert order is newest first
3. test_get_job_cv_returns_404_when_file_missing
   — seed a job with a cv_path that doesn't exist on disk, assert 404 response
4. test_get_job_cover_letter_returns_404_when_file_missing
   — same for cover letter
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(tmp_path, monkeypatch):
    """Return a TestClient backed by a fresh temp DB."""
    import main as m
    import database

    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    database.init_db(db_path)

    return TestClient(m.app), db_path


# ---------------------------------------------------------------------------
# 1. GET /runs returns [] when DB has no runs
# ---------------------------------------------------------------------------

def test_get_runs_returns_empty_list_when_no_runs(tmp_path, monkeypatch):
    client, _ = _make_client(tmp_path, monkeypatch)

    response = client.get("/runs")

    assert response.status_code == 200
    data = response.json()
    assert data == []


# ---------------------------------------------------------------------------
# 2. GET /runs returns runs newest first
# ---------------------------------------------------------------------------

def test_get_runs_returns_runs_newest_first(tmp_path, monkeypatch):
    client, db_path = _make_client(tmp_path, monkeypatch)

    # Seed two runs: older first, newer second
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-01-01T10:00:00+00:00", 5, 3, 2, "complete"),
    )
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-06-28T10:00:00+00:00", 10, 7, 4, "complete"),
    )
    conn.commit()
    conn.close()

    response = client.get("/runs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Newest run (higher id, date 2026-06-28) should be first
    assert data[0]["date"] == "2026-06-28T10:00:00+00:00"
    assert data[1]["date"] == "2026-01-01T10:00:00+00:00"


# ---------------------------------------------------------------------------
# 3. GET /runs/{run_id}/jobs/{job_id}/cv returns 404 when file missing
# ---------------------------------------------------------------------------

def test_get_job_cv_returns_404_when_file_missing(tmp_path, monkeypatch):
    client, db_path = _make_client(tmp_path, monkeypatch)

    # Seed a run and a job with a cv_path that doesn't exist on disk
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-06-28T10:00:00+00:00", 1, 1, 1, "complete"),
    )
    run_id = cursor.lastrowid
    non_existent_path = str(tmp_path / "nonexistent_cv.txt")
    cursor.execute(
        """INSERT INTO jobs (run_id, title, company, location, score, reasoning, selected, cv_path, cover_letter_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, "Python Developer", "ACME", "Paris", 8.0, "Good fit.", 1,
         non_existent_path, str(tmp_path / "nonexistent_cl.txt")),
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    response = client.get(f"/runs/{run_id}/jobs/{job_id}/cv")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# ---------------------------------------------------------------------------
# 4. GET /runs/{run_id}/jobs/{job_id}/cover-letter returns 404 when file missing
# ---------------------------------------------------------------------------

def test_get_job_cover_letter_returns_404_when_file_missing(tmp_path, monkeypatch):
    client, db_path = _make_client(tmp_path, monkeypatch)

    # Seed a run and a job with a cover_letter_path that doesn't exist on disk
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (date, jobs_found, jobs_after_filter, jobs_selected, status) VALUES (?, ?, ?, ?, ?)",
        ("2026-06-28T10:00:00+00:00", 1, 1, 1, "complete"),
    )
    run_id = cursor.lastrowid
    non_existent_path = str(tmp_path / "nonexistent_cover_letter.txt")
    cursor.execute(
        """INSERT INTO jobs (run_id, title, company, location, score, reasoning, selected, cv_path, cover_letter_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, "Backend Engineer", "Beta Corp", "Lyon", 7.0, "Good fit.", 1,
         str(tmp_path / "nonexistent_cv.txt"), non_existent_path),
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    response = client.get(f"/runs/{run_id}/jobs/{job_id}/cover-letter")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()
