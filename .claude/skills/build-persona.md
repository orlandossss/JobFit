# Skill: build-persona

You are conducting a structured interview to build a professional persona profile for the user. Your goal is to gather comprehensive information about their background, skills, and career goals, then synthesize everything into a `persona.json` file at the repo root.

## Interview Process

Conduct the interview conversationally. Ask questions one topic at a time (or a small cluster of related questions). Wait for the user's answer before moving on. Ask meaningful follow-up questions — do not accept vague or surface-level answers.

### Topics to cover (adapt order to the conversation flow)

1. **Basic info** — Full name, location (city/country), preferred languages (spoken/written)
2. **Current situation** — Are you currently employed? What is your current role and company (if any)?
3. **Work experience** — Walk me through your career history. For each role: company, title, duration, key responsibilities, notable achievements.
4. **Skills** — Technical skills (languages, frameworks, tools, platforms), soft skills, domain expertise. For each technical skill, ask approximate years of experience and proficiency level (beginner / intermediate / advanced / expert).
5. **Education** — Degrees, institutions, graduation years, relevant coursework or certifications.
6. **Target roles** — What kinds of roles are you looking for? Job titles, seniority level, industries.
7. **Work preferences** — Preferred work arrangement: remote, hybrid, or on-site? Full-time or part-time? Contract or permanent?
8. **Salary expectations** — What is your target annual salary or hourly rate? What currency? Are you flexible?
9. **Location preferences** — Are you open to relocation? Which cities/countries are acceptable?
10. **Availability** — When can you start? Notice period?
11. **Values and culture** — What kind of team/company culture do you thrive in? Anything you want to avoid?
12. **Portfolio / links** — GitHub, LinkedIn, personal website, portfolio URL, etc.
13. **Anything else** — Is there anything important about you that would not fit the categories above?

## Follow-up guidance

- If an answer is vague ("I know Python"), probe deeper ("Roughly how many years? What have you built with it? What libraries do you use most?").
- If the user mentions a technology or achievement, ask for specifics.
- Do not rush through the list — quality over speed.

## Synthesizing the persona

Once you have gathered enough information (or the user signals they are done), synthesize everything into a JSON object. The fields should be dynamic — use whatever fields make sense given the conversation. Suggested structure (adapt freely):

```json
{
  "name": "...",
  "location": "...",
  "languages_spoken": ["..."],
  "current_role": "...",
  "experience_years_total": 0,
  "work_history": [
    {
      "company": "...",
      "title": "...",
      "start": "YYYY-MM",
      "end": "YYYY-MM or present",
      "highlights": ["..."]
    }
  ],
  "skills": {
    "technical": [
      { "name": "...", "level": "expert|advanced|intermediate|beginner", "years": 0 }
    ],
    "soft": ["..."],
    "domains": ["..."]
  },
  "education": [
    {
      "degree": "...",
      "institution": "...",
      "year": "..."
    }
  ],
  "certifications": ["..."],
  "target_roles": ["..."],
  "target_industries": ["..."],
  "work_arrangement_preference": "remote|hybrid|on-site|flexible",
  "employment_type_preference": "permanent|contract|either",
  "salary_expectation": {
    "amount": 0,
    "currency": "USD",
    "period": "annual|hourly"
  },
  "location_preferences": {
    "open_to_relocation": true,
    "preferred_locations": ["..."]
  },
  "availability": "...",
  "culture_values": ["..."],
  "portfolio_links": {
    "github": "...",
    "linkedin": "...",
    "website": "..."
  },
  "notes": "..."
}
```

Omit fields for which you have no information. Add fields that capture important details not covered above.

## Saving the file

Write the final JSON to `persona.json` at the **repo root** (i.e., the directory that contains `backend/` and `frontend/`).

After saving, confirm to the user:

> "Your persona has been saved to `persona.json`. You can view it in the web UI by navigating to the **Persona** page (open the app at http://localhost:5173 and click the Persona link in the navigation)."
