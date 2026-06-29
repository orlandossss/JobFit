"""
JobFit scoring agent.

score_job() receives a persona dict and a job dict, calls the LLM, and
returns {"score": int, "reasoning": str}.  The LLM call is isolated behind
llm.call_llm so tests can patch it without loading a real model.
"""
import json
import re

from llm import call_llm

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
