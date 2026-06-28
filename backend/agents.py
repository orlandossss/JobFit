"""
JobFit agents: scoring, CV rewriting, and cover letter generation.

Each agent receives a minimal context (persona summary + base document +
job info) to stay within 7B–13B model context windows.

The LLM call is isolated behind llm.call_llm so tests can patch it
without loading a real model.
"""
import json
import re

from llm import call_llm

# ---------------------------------------------------------------------------
# Scoring agent
# ---------------------------------------------------------------------------

SCORE_PROMPT = """You are a job-fit evaluator. Given a candidate profile and a job listing, output a JSON object with two fields:
- "score": integer 1-10 (10 = perfect fit)
- "reasoning": one sentence explaining the score

Candidate profile:
{persona_summary}

Job title: {title}
Job description (excerpt):
{description}

Respond with ONLY valid JSON, no other text. Example: {{"score": 7, "reasoning": "Strong Python match but requires 5+ years senior experience."}}"""

# Persona fields forwarded to the LLM — keeps context minimal for 7B–13B models
_PERSONA_FIELDS = [
    "skills",
    "experience_years",
    "target_titles",
    "education",
    "languages",
    "work_preference",
]


def score_job(persona: dict, job: dict) -> dict:
    """Score *job* against *persona*.

    Returns a dict with:
      - ``score``    (int 1–10, 0 on parse failure)
      - ``reasoning`` (str, one sentence)
    """
    persona_summary = json.dumps(
        {k: v for k, v in persona.items() if k in _PERSONA_FIELDS},
        indent=2,
        ensure_ascii=False,
    )
    description_excerpt = (job.get("description") or "")[:1500]
    prompt = SCORE_PROMPT.format(
        persona_summary=persona_summary,
        title=job.get("title", ""),
        description=description_excerpt,
    )
    raw = call_llm(prompt)

    # Parse JSON defensively — the model may include extra prose
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"score": 0, "reasoning": "Failed to parse LLM response"}
    try:
        result = json.loads(match.group())
        return {
            "score": int(result.get("score", 0)),
            "reasoning": str(result.get("reasoning", "")),
        }
    except Exception:
        return {"score": 0, "reasoning": "Failed to parse LLM response"}


# ---------------------------------------------------------------------------
# CV rewriter agent
# ---------------------------------------------------------------------------

CV_PROMPT = """You are an expert CV writer. Rewrite the following CV to better match the job listing below.
Keep the same person's real experience — do not invent anything. Emphasise relevant skills and experience.
Output ONLY the rewritten CV text, no commentary.

Candidate profile summary:
{persona_summary}

Job title: {title}
Job description (excerpt):
{description}

Original CV:
{base_cv}

Rewritten CV:"""


def rewrite_cv(persona: dict, base_cv: str, job: dict) -> str:
    """Rewrite *base_cv* to better match *job* for the given *persona*.

    Returns the tailored plain-text CV string.
    """
    persona_summary = json.dumps(
        {k: v for k, v in persona.items() if k in _PERSONA_FIELDS},
        indent=2,
        ensure_ascii=False,
    )
    description_excerpt = (job.get("description") or "")[:1500]
    prompt = CV_PROMPT.format(
        persona_summary=persona_summary,
        title=job.get("title", ""),
        description=description_excerpt,
        base_cv=base_cv,
    )
    return call_llm(prompt, max_tokens=1024)


# ---------------------------------------------------------------------------
# Cover letter writer agent
# ---------------------------------------------------------------------------

COVER_LETTER_PROMPT = """You are an expert cover letter writer. Write a tailored cover letter for the job below.
Use the candidate's real background. Be specific and compelling. Output ONLY the cover letter text.

Candidate profile summary:
{persona_summary}

Job title: {title}
Company: {company}
Job description (excerpt):
{description}

Base cover letter for reference:
{base_cover_letter}

Tailored cover letter:"""


def write_cover_letter(persona: dict, base_cover_letter: str, job: dict) -> str:
    """Write a tailored cover letter for *job* based on *base_cover_letter*.

    Returns the tailored plain-text cover letter string.
    """
    persona_summary = json.dumps(
        {k: v for k, v in persona.items() if k in _PERSONA_FIELDS},
        indent=2,
        ensure_ascii=False,
    )
    description_excerpt = (job.get("description") or "")[:1500]
    prompt = COVER_LETTER_PROMPT.format(
        persona_summary=persona_summary,
        title=job.get("title", ""),
        company=job.get("company", ""),
        description=description_excerpt,
        base_cover_letter=base_cover_letter,
    )
    return call_llm(prompt, max_tokens=1024)
