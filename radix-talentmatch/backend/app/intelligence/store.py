"""Persistence for researched companies + the offline fallback.

Artifacts land in `<ROOT>/data/company_intelligence/<slug>/` so a demo works
after research has run once, and Talent Check can show a verified badge:

* `research_bundle.json`     – the merged bundle the API serves and the UI reads
* `research_<provider>.json` – raw parsed rows per provider (reloadable for
                               surgical consolidation retries — Level-4 style)
* `data_quality_report.md`   – the offline gate's markdown report

When no LLM keys are configured, `fallback_expectation_matrix` /
`fallback_hiring` synthesize plausible, clearly-labelled artifacts from the
bundled illustrative skills JSON — never presented as verified.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from app.intelligence.quality import SKILL_CODES, SKILL_COLUMNS

ROOT = Path(__file__).resolve().parents[3]  # backend/app/intelligence -> repo root


def store_root() -> Path:
    p = os.getenv("RADIX_INTEL_PATH")
    if p:
        raw = Path(p)
        return raw if raw.is_absolute() else (ROOT / raw).resolve()
    return ROOT / "data" / "company_intelligence"


def slugify(company: str) -> str:
    import re
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", company.lower())).strip("-") or "company"


def company_dir(company: str, create: bool = False) -> Path:
    d = store_root() / slugify(company)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def save_artifacts(company: str, bundle: dict) -> Path:
    d = company_dir(company, create=True)
    (d / "research_bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    if bundle.get("quality_report_md"):
        (d / "data_quality_report.md").write_text(bundle["quality_report_md"], encoding="utf-8")
    return d


def save_provider_research(company: str, provider: str, payload: dict) -> Path:
    d = company_dir(company, create=True)
    path = d / f"research_{provider}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def load_provider_research(company: str, provider: str) -> dict | None:
    path = company_dir(company) / f"research_{provider}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def load_research(company: str) -> dict | None:
    path = company_dir(company) / "research_bundle.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def load_bundle_dir(directory: Path) -> dict | None:
    path = directory / "research_bundle.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def verified_list() -> list[dict]:
    """All companies with a stored bundle, newest first."""
    root = store_root()
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        bundle = load_bundle_dir(d)
        if not bundle:
            continue
        q = bundle.get("quality", {})
        out.append({
            "company": bundle.get("company") or d.name,
            "mode": bundle.get("mode"),
            "verified": bundle.get("verified", False),
            "errors": q.get("errors", 0),
            "warnings": q.get("warnings", 0),
            "researched_at": bundle.get("researched_at"),
        })
    return out


def snapshot_files() -> dict:
    """Load the bundled demo intelligence snapshot (offline default)."""
    base = store_root() / "_bundled"
    files = {}
    for name in ("expectation_matrix.json", "hiring_rounds.json", "golden_record.json"):
        p = base / name
        if p.exists():
            try:
                files[name.replace(".json", "")] = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                continue
    return files


# --------------------------------------------------------------- fallback ----

SKILL_CODE_BY_KEYWORD = [
    ("DSA", lambda n: "algorithm" in n or "data structure" in n),
    ("OOD", lambda n: "object" in n or "design pattern" in n),
    ("APTI", lambda n: "aptitude" in n or "reasoning" in n or "problem" in n),
    ("COMM", lambda n: "communication" in n or "english" in n),
    ("AI", lambda n: "machine learning" in n or n.startswith("ai") or "deep learning" in n),
    ("CLOUD", lambda n: "cloud" in n or "aws" in n or "azure" in n or "devops" in n or "docker" in n),
    ("SQL", lambda n: "sql" in n or "database" in n or "postgresql" in n or "mysql" in n),
    ("SWE", lambda n: "software engineering" in n or "git" in n or "testing" in n or "api" in n),
    ("SYSD", lambda n: "system design" in n or "distributed" in n),
    ("NETW", lambda n: "network" in n or "tcp" in n),
    ("OS", lambda n: "operating" in n or "linux" in n),
]

_COLUMN_FOR_SKILL_CODE = {
    "COD": "coding", "DSA": "data_structures_and_algorithms",
    "OOD": "object_oriented_programming_and_design", "APTI": "aptitude_and_problem_solving",
    "COMM": "communication_skills", "AI": "ai_native_engineering", "CLOUD": "devops_and_cloud",
    "SQL": "sql_and_design", "SWE": "software_engineering",
    "SYSD": "system_design_and_architecture", "NETW": "computer_networking", "OS": "operating_system",
}


def _code_for(name: str) -> str:
    low = name.lower()
    for code, pred in SKILL_CODE_BY_KEYWORD:
        if pred(low):
            return code
    return "COD"


def generic_expectations() -> dict[str, tuple[int, str]]:
    """Clearly-generic campus bar for companies we have no verified view of."""
    return {
        "COD": (7, "AP"), "DSA": (7, "AS"), "OOD": (5, "AP"), "APTI": (6, "AP"),
        "COMM": (5, "CU"), "AI": (4, "AP"), "CLOUD": (4, "CU"), "SQL": (6, "AP"),
        "SWE": (6, "AP"), "SYSD": (5, "EV"), "NETW": (4, "CU"), "OS": (5, "CU"),
    }


def generic_expectations_by_column() -> dict[str, tuple[int, str]]:
    """Same generic bar, keyed by expectation-matrix column name."""
    by_code = generic_expectations()
    return {col: by_code[code] for code, col in _COLUMN_FOR_SKILL_CODE.items()}


def fallback_expectation_matrix(company: str, company_data: dict) -> dict:
    """Offline Level-Code row, labelled as an unverified illustrative snapshot."""
    companies = (company_data or {}).get("companies", {})
    chosen = next((c for c in companies if c.lower() == company.lower()), None)
    if chosen is None:
        chosen = next((c for c in companies if company.lower() in c.lower() or c.lower() in company.lower()), None)

    generics = generic_expectations_by_column()
    tokens = {}
    if chosen:
        for req in companies.get(chosen, []):
            code = req.get("category_code") or _code_for(req.get("skill_name", ""))
            col = _COLUMN_FOR_SKILL_CODE.get(code)
            if col:
                tokens[col] = {"level": int(req.get("required_level", 5)), "bloom_code": "AP",
                               "raw": f"{int(req.get('required_level', 5))}-AP", "generic": True}
    for col in SKILL_COLUMNS:
        if col not in tokens:
            level, bloom = generics[col]
            tokens[col] = {"level": level, "bloom_code": bloom,
                           "raw": f"{level}-{bloom}", "generic": True}
    return {"companies": chosen or company, "tokens": tokens}


def fallback_hiring(company: str, company_data: dict) -> dict:
    """Canonical hiring envelope, offline illustrative shape."""
    companies = (company_data or {}).get("companies", {})
    chosen = next((c for c in companies if c.lower() == company.lower()), None)
    rounds = [
        {"round_number": 1, "round_name": "Coding Test", "round_category": "Coding Test",
         "evaluation_type": "Technical", "assessment_mode": "Online",
         "skill_sets": [
             {"skill_set_code": "DSA", "typical_questions": "Generic practice task; research this company to replace this snapshot."},
             {"skill_set_code": "COD", "typical_questions": "Implement a small utility function."},
         ]},
        {"round_number": 2, "round_name": "Technical Interview", "round_category": "Interview",
         "evaluation_type": "Technical", "assessment_mode": "Onsite",
         "skill_sets": [
             {"skill_set_code": "SYSD", "typical_questions": "Design a small system end to end."},
             {"skill_set_code": "OOD", "typical_questions": "Model a familiar domain using objects."},
         ]},
        {"round_number": 3, "round_name": "HR Interview", "round_category": "Interview",
         "evaluation_type": "HR", "assessment_mode": "Onsite",
         "skill_sets": [
             {"skill_set_code": "COMM", "typical_questions": "Tell me about a project you led."},
         ]},
    ]
    return {
        "company_name": chosen or company,
        "job_role_details": [{
            "opportunity_type": "Employment",
            "role_title": "Software Engineer (illustrative)",
            "role_category": "SDE",
            "job_description": f"Illustrative offline snapshot for {chosen or company}; run the LangGraph research pipeline for verified data.",
            "compensation": "Not publicly standardised",
            "ctc_or_stipend": 0,
            "bonus": "Not publicly known",
            "benefits_summary": "Not publicly known",
            "hiring_rounds": rounds,
        }],
    }


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


def duration_ms(start: float) -> int:
    return int((time.time() - start) * 1000)
