"""
JobFit FastAPI backend entry point.
"""
import json
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database

# Path to the search config file (relative to the repo root, one level above backend/)
SEARCH_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "search_config.json")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
