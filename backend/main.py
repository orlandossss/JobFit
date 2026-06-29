"""
JobFit FastAPI backend entry point.
"""
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Generator, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import database
from agents import score_job

# Lazy import — resolved at call time so the module can be loaded without jobspy
# installed (e.g. in unit-test environments). Tests patch ``main.scrape_jobs``.
try:
    from jobspy import scrape_jobs
except ImportError:  # pragma: no cover — only happens when jobspy is absent

    def scrape_jobs(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError(
            "python-jobspy is not installed. Run: pip install python-jobspy"
        )

# Path to the search config file (relative to the repo root, one level above backend/)
SEARCH_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "search_config.json")

# Paths validated before each pipeline run (relative to repo root)
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
PERSONA_PATH = os.path.join(REPO_ROOT, "persona.json")
BASE_CV_PATH = os.path.join(REPO_ROOT, "input", "base_cv.txt")
BASE_COVER_LETTER_PATH = os.path.join(REPO_ROOT, "input", "base_cover_letter.txt")

# Sensible defaults returned when search_config.json does not exist
_SEARCH_CONFIG_DEFAULTS = {
    "target_titles": [],
    "location": "",
    "country": "",
    "language": "en",
    "keywords_include": [],
    "keywords_exclude": [],
    "max_jobs": 5,
}


class SearchConfig(BaseModel):
    target_titles: List[str] = []
    location: str = ""
    country: str = ""
    language: str = "en"
    keywords_include: List[str] = []
    keywords_exclude: List[str] = []
    max_jobs: int = 5


def filter_jobs(jobs: list[dict], config: dict) -> list[dict]:
    """Pure keyword pre-filter.

    Include logic: if ``keywords_include`` is non-empty, a job must have at
    least one keyword (case-insensitive) in its title or description to pass.
    If the list is empty, all jobs pass the include step.

    Exclude logic: if ``keywords_exclude`` is non-empty, a job is dropped if
    its title or description contains any of those keywords (case-insensitive).
    If the list is empty, nothing is dropped.
    """
    include_kws = [k.lower() for k in config.get("keywords_include", []) if k]
    exclude_kws = [k.lower() for k in config.get("keywords_exclude", []) if k]

    filtered = []
    for job in jobs:
        text = " ".join(
            str(job.get(field) or "") for field in ("title", "description")
        ).lower()

        if include_kws and not any(kw in text for kw in include_kws):
            continue
        if exclude_kws and any(kw in text for kw in exclude_kws):
            continue

        filtered.append(job)

    return filtered


def _sse_event(payload: dict) -> str:
    """Format a single SSE data line."""
    return f"data: {json.dumps(payload)}\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the SQLite database on startup."""
    database.init_db()
    yield


app = FastAPI(title="JobFit", version="0.1.0", lifespan=lifespan)

# Allow the React dev server to reach the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.get("/search-config", response_model=SearchConfig)
def get_search_config() -> SearchConfig:
    """Return the current search configuration.

    If search_config.json does not exist, returns sensible empty defaults.
    """
    if not os.path.exists(SEARCH_CONFIG_PATH):
        return SearchConfig(**_SEARCH_CONFIG_DEFAULTS)

    with open(SEARCH_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return SearchConfig(**{**_SEARCH_CONFIG_DEFAULTS, **data})


@app.put("/search-config", response_model=SearchConfig)
def put_search_config(config: SearchConfig) -> SearchConfig:
    """Write updated search configuration to disk and return the saved config."""
    config_data = config.model_dump()

    os.makedirs(os.path.dirname(os.path.abspath(SEARCH_CONFIG_PATH)), exist_ok=True)

    with open(SEARCH_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    return config


@app.post("/run")
def run_pipeline() -> StreamingResponse:
    """Start the job-search pipeline and stream progress via SSE."""

    def _stream() -> Generator[str, None, None]:
        # ── Pre-run validation ───────────────────────────────────────────────
        missing = []
        for label, path in [
            ("persona.json", PERSONA_PATH),
            ("input/base_cv.txt", BASE_CV_PATH),
            ("input/base_cover_letter.txt", BASE_COVER_LETTER_PATH),
        ]:
            if not os.path.exists(path):
                missing.append(label)

        if missing:
            yield _sse_event({
                "event": "run_failed",
                "message": f"Missing required files: {', '.join(missing)}",
            })
            return

        yield _sse_event({"event": "run_started"})

        # ── Load search config ────────────────────────────────────────────────
        if os.path.exists(SEARCH_CONFIG_PATH):
            with open(SEARCH_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = {**_SEARCH_CONFIG_DEFAULTS, **json.load(f)}
        else:
            config = dict(_SEARCH_CONFIG_DEFAULTS)

        yield _sse_event({"event": "scraping_started"})

        # ── Scrape ────────────────────────────────────────────────────────────
        try:
            titles = config.get("target_titles", [])
            search_term = " OR ".join(titles) if titles else ""
            df = scrape_jobs(
                site_name=["indeed"],
                search_term=search_term,
                location=config.get("location", ""),
                results_wanted=200,
                hours_old=24,
                country_indeed=config.get("country", ""),
            )

            # Normalise to list[dict] — jobspy returns a DataFrame
            if hasattr(df, "to_dict"):
                raw_jobs = df.to_dict(orient="records")
            elif isinstance(df, list):
                raw_jobs = df
            else:
                raw_jobs = list(df)

        except Exception as exc:
            yield _sse_event({"event": "run_failed", "message": str(exc)})
            return

        # ── Store raw jobs ────────────────────────────────────────────────────
        conn = sqlite3.connect(database.DEFAULT_DB_PATH)
        cursor = conn.cursor()

        # Create a placeholder run record so we have a run_id for the jobs
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO runs (date, jobs_found, jobs_after_filter, status) VALUES (?, ?, ?, ?)",
            (now_iso, len(raw_jobs), 0, "scraping"),
        )
        run_id = cursor.lastrowid

        for job in raw_jobs:
            cursor.execute(
                """INSERT INTO jobs
                   (run_id, title, company, location, description, url, salary)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    str(job.get("title") or ""),
                    str(job.get("company") or ""),
                    str(job.get("location") or ""),
                    str(job.get("description") or ""),
                    str(job.get("job_url") or job.get("url") or ""),
                    str(job.get("min_amount") or job.get("salary") or ""),
                ),
            )

        conn.commit()

        yield _sse_event({"event": "scraping_complete", "count": len(raw_jobs)})

        # ── Keyword pre-filter ────────────────────────────────────────────────
        filtered = filter_jobs(raw_jobs, config)

        # Update run record with post-filter count
        cursor.execute(
            "UPDATE runs SET jobs_found = ?, jobs_after_filter = ?, status = ? WHERE id = ?",
            (len(raw_jobs), len(filtered), "scraped", run_id),
        )
        conn.commit()
        conn.close()

        yield _sse_event({"event": "filtering_complete", "count": len(filtered)})

        # ── LLM scoring ───────────────────────────────────────────────────────
        with open(PERSONA_PATH, "r", encoding="utf-8") as f:
            persona = json.load(f)

        conn = sqlite3.connect(database.DEFAULT_DB_PATH)
        cursor = conn.cursor()

        # Fetch the DB rows for filtered jobs so we can update score/reasoning.
        # We match by run_id + title (good enough — titles are unique per scrape).
        # Cap at 50 to avoid excessively long runs.
        jobs_to_score = filtered[:50]

        scored_jobs = []  # list of (db_id, score) for ranking
        for job in jobs_to_score:
            result = score_job(persona, job)
            score_val = result["score"]
            reasoning_val = result["reasoning"]

            # Locate the job row in SQLite (run_id + title is the natural key here)
            cursor.execute(
                "SELECT id FROM jobs WHERE run_id = ? AND title = ? LIMIT 1",
                (run_id, str(job.get("title") or "")),
            )
            row = cursor.fetchone()
            if row:
                db_id = row[0]
                cursor.execute(
                    "UPDATE jobs SET score = ?, reasoning = ? WHERE id = ?",
                    (score_val, reasoning_val, db_id),
                )
                scored_jobs.append((db_id, score_val))

            yield _sse_event({
                "event": "scoring_job",
                "title": str(job.get("title") or ""),
                "score": score_val,
            })

        conn.commit()

        # ── Select top N ──────────────────────────────────────────────────────
        max_jobs = int(config.get("max_jobs", 5))
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        top_n = scored_jobs[:max_jobs]

        for db_id, _ in top_n:
            cursor.execute("UPDATE jobs SET selected = 1 WHERE id = ?", (db_id,))

        # Update run record
        cursor.execute(
            "UPDATE runs SET jobs_selected = ?, status = ? WHERE id = ?",
            (len(top_n), "scored", run_id),
        )
        conn.commit()
        conn.close()

        yield _sse_event({"event": "scoring_complete", "count": len(top_n)})
        yield _sse_event({"event": "run_complete", "run_id": run_id})

    return StreamingResponse(_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
