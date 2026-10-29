# Testing

Run backend tests from `backend/` with `python -m pytest -q` (Windows: `py -m pytest -q`). The test module sets `RADIX_DB_PATH` to a temporary SQLite file before importing the app, isolating tests from `backend/profiles.db`.

Coverage includes health, JD text analysis, unsupported/empty input validation, resume parsing, profile create/read/update persistence, readiness schema and score bounds, missing skills, and different candidates/job descriptions yielding different match scores. Frontend build validation can be run from `frontend/` with `npm install` followed by `npm run build`.


Additional regressions cover canonical DSA/OOP/JS/ML aliases, separation of Java from JavaScript and React from JavaScript, extraction normalization, unrated detected skills remaining unassessed, and SQLite assessment-history writes.
