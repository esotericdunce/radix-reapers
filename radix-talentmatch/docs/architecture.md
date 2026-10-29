# Architecture

The local app has a Vite/React UI and a single FastAPI service. The UI calls the backend through `frontend/src/services/api.ts`; the API owns profile persistence and serves demo JSON records. No credentials or external AI are required.

## Components

- `backend/app/main.py`: route composition, JSON data loading, seed-on-startup, request/response orchestration.
- `backend/app/services/document_extractor.py`: size/type validation and PDF/DOCX/TXT extraction.
- `backend/app/services/skill_extractor.py`: Pydantic-validated taxonomy and boundary-aware phrase extraction.
- `backend/app/repositories/profile_repository.py`: SQLite profile repository; set `RADIX_DB_PATH` to relocate.
- `backend/app/utils/scoring.py`: normalized exact-name comparisons and scoring.
- `data/*.json`: synthetic candidate/job snapshots and illustrative company requirements.
- `frontend/src/pages/Modules.tsx`: six page workflows; API errors are shown to users.

## Skill taxonomy

Supported codes: COD (Coding), DSA (Data Structures & Algorithms), OOD (Object-Oriented Design), APTI (Aptitude), COMM (Communication), AI (Artificial Intelligence), CLOUD (Cloud), SQL (SQL), SWE (Software Engineering), SYSD (System Design), NETW (Networking), OS (Operating Systems), OTHER (Other skills). Extracted skills include `skill_name`, `category_code`, `evidence`, and confidence (`high`, `medium`, or `low`). Pydantic validates category and confidence values.

## Storage strategy

Profiles are JSON payloads in a SQLite table keyed by stable candidate ID. Startup inserts sample profiles only when their IDs are absent, preserving saved changes. Jobs and company expectations remain JSON snapshots to make replacing demo data straightforward. The local repository can later be replaced by an adapter without changing the scoring formulas.

## Scoring

Profile levels are 1–10 and default to 5 only in manually entered parser skills; an absent skill has level 0. For each company requirement, contribution is `min(candidate_level, required_level) / required_level`; readiness is mean contribution × 100, rounded, and clamped to 0–100. Job matching checks exact normalized skill names: score is matched required phrases / all extracted required phrases × 100. Missing skills produce improvement recommendations. Scores are rules-based, not predictive hiring judgments.

Company JSON has a `source` label. Included expectations are fictional/illustrative and must not be described as official.
