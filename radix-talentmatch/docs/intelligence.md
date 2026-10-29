# Company Intelligence Lab — the "Verified Data" differentiator

Every team was handed the same Session Materials (metadata-driven testing,
multi-LLM research agents, LangGraph gates). Teams either ignore them or run
the published Level-4 scripts out-of-band and paste a CSV. RADIX TalentMatch
instead makes the *pipeline itself a product feature*, end to end:

```
JD text ──► deterministic extraction (unchanged, no LLM)
Company  ──► research fan-out (OpenRouter + Groq + Gemini)
         ──► consensus agent (majority vote per skill, conflicts kept visible)
         ──► 12-skill × Bloom(Level-Code) expectation matrix
         ──► hiring-rounds agent (round-by-round, skills_tested, questions)
         ──► offline quality gate (Level-3-style rules, expanded per artifact)
         ──► persisted research bundle (data/company_intelligence/<slug>/)
Talent Check ──► prefers VERIFIED bundles; shows a verification panel
```

## What judges see

- **Company Intel page** (`/company-intel`): type any company → agents run →
  pipeline trace with per-stage timing, skill-matrix table with Bloom depth +
  per-skill confidence + source agreement, hiring-round timeline with the exact
  skills each round tests, and the full data-quality gate report (errors shown,
  never hidden). LLM-to-LLM disagreements render as a conflict panel.
- **Talent Check gets a verification banner**: green "Verified company research
  (N LLM agents in consensus)" or amber "Unverified offline snapshot", with the
  gate's error/warning counts. The readiness score silently upgrades to the
  researched 12-skill bar once a bundle exists.
- **Offline-first, zero keys needed**: no `OPENROUTER_API_KEY`/`GROQ_API_KEY`/
  `GEMINI_API_KEY` in `.env` → a clearly-labelled illustrative fallback snapshot
  runs the exact same gate and persistence path, so the demo can't die.
- **⌘K command palette**: jump to any module or researched dossier; typed-port
  of the placement-hub palette, dependency-free.
- **NeoPOP UI**: CRED's `@cred/neopop-web` ElevatedCard + dark NeoPOP palette
  (signal `#F2C14E`), borrowed from the sibling placement-hub project.

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /api/intelligence/status` | provider availability + stored bundles |
| `POST /api/intelligence/research {company}` | run the whole pipeline (surgical retry per stage, ≤2 retries) |
| `GET /api/intelligence/company/{name}` | reload a stored dossier |
| `GET /api/intelligence/supabase/companies` | read `company_json` from the team's Supabase (set `SUPABASE_URL` + `SUPABASE_ANON_KEY`) |
| `POST /api/talent-check` | now answers with a `verification` block |

## Module map

```
backend/app/intelligence/
  prompts.py            — self-contained Level-4-style agent prompts (JSON-only)
  providers.py          — three REST LLM brains + OpenRouter failover slot
  consensus.py          — messy-JSON extraction + majority-vote consolidation
  quality.py            — rule registry (Levels in range, Bloom codes, placeholder,
                          formatting, matrix completeness/flatness, rounds shape)
                          + quality verdict + markdown report
  agents.py             — pipeline runner w/ per-stage surgical retry
  store.py              — artifact persistence + bundled offline fallback
  supabase_source.py    — optional PostgREST reader for company_json
```

Artifacts persist to `data/company_intelligence/<slug>/research_bundle.json`
(override with `RADIX_INTEL_PATH`), so research survives restarts and demos run
against stored, gate-approved data.

## Tests

`backend/tests/test_intelligence.py` — 13 offline tests: gate rules (range,
Bloom, placeholders, flat/short matrices, bad rounds), JSON extraction under
fences/prose, majority-vote consensus with conflict recording, the full
offline fallback pipeline through the HTTP API, talent-check preference order
(verified beats static demo data), and category-code-based readiness scoring.
Run: `.venv/bin/python -m pytest -q`.
