# API reference

Base URL: `http://localhost:8000`; interactive OpenAPI UI: `/docs`.

- `GET /api/health` → `{status, version}`.
- `GET /api/candidates` and `/api/profiles` → candidate profile array.
- `GET /api/jobs` → synthetic job description array.
- `GET /api/companies` → available company names and expectation source label.
- `POST /api/jd/analyze` and `POST /api/resume/parse` accept multipart `file` (PDF/DOCX/TXT) or form `text`. Upload size limit is 8 MB. Unsupported types return 415; invalid/empty documents return 422.
- `GET /api/profile?candidate_id=<id>` → profile (without ID, first profile); `POST /api/profile` creates a profile; `PUT /api/profile?candidate_id=<id>` updates an existing profile. IDs are stable strings. Duplicate creation returns 409; missing update target returns 404.
- `POST /api/talent-check` JSON: `{ "candidate_id": "ananya-rao", "company": "Google" }`. Returns company source, readiness score 0–100, skill gaps, and recommendations.
- `POST /api/skill-match` JSON: `{ "candidate_id": "ananya-rao", "job_description_id": "google-swe" }`, or include `job_description` instead. Returns matched/missing skills, category breakdown, score 0–100, and recommendations.

Document files are read only; the API does not execute uploads. PDF extraction uses PyMuPDF; DOCX uses python-docx. CORS defaults to local Vite origins and can be configured using `CORS_ORIGINS`.


## Assessment history

`GET /api/assessments?limit=50` returns newest-first real Talent Check and Skill Match API calls persisted in local SQLite (1–200 records). Each record includes `type`, candidate ID/name, target, score, and UTC timestamp. `POST /api/talent-check` and `POST /api/skill-match` append an event only after a successful calculation.
