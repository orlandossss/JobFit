"""
Tests for Issue #1: Project scaffold.
- Health-check endpoint returns 200
- SQLite database initializes with the correct tables (runs, jobs) on startup
"""
import sqlite3
import tempfile
import os
import pytest
from fastapi.testclient import TestClient


def test_health_check_returns_200():
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_database_initializes_with_correct_tables():
    """Database init creates runs and jobs tables with the expected columns."""
    import database

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        database.init_db(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check runs table exists with expected columns
        cursor.execute("PRAGMA table_info(runs)")
        runs_cols = {row[1] for row in cursor.fetchall()}
        assert runs_cols == {
            "id", "date", "jobs_found", "jobs_after_filter",
            "jobs_selected", "status"
        }, f"Unexpected runs columns: {runs_cols}"

        # Check jobs table exists with expected columns
        cursor.execute("PRAGMA table_info(jobs)")
        jobs_cols = {row[1] for row in cursor.fetchall()}
        assert jobs_cols == {
            "id", "run_id", "title", "company", "location", "description",
            "url", "salary", "score", "reasoning", "selected",
            "cv_path", "cover_letter_path"
        }, f"Unexpected jobs columns: {jobs_cols}"

        conn.close()
