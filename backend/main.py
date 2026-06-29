"""
JobFit FastAPI backend entry point.
"""
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import database

# Default persona.json lives at the repo root (one level above backend/).
# Tests override this via the PERSONA_PATH environment variable.
_DEFAULT_PERSONA_PATH = Path(__file__).parent.parent / "persona.json"


def _persona_path() -> Path:
    env_override = os.environ.get("PERSONA_PATH")
    return Path(env_override) if env_override else _DEFAULT_PERSONA_PATH


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


@app.get("/persona")
def get_persona() -> dict:
    """Return the contents of persona.json.

    Returns 200 + JSON when persona.json exists.
    Returns 404 with a helpful message when it is missing.
    """
    path = _persona_path()
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "persona.json not found. "
                "Run the build-persona skill in Claude Code to create your persona: "
                "type /build-persona in Claude Code and follow the interview prompts."
            ),
        )
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
