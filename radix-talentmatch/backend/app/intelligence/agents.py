"""The Company Intelligence pipeline — a real LangGraph state machine.

Topology (Level-5 canonical, implemented in this product instead of a script):

    research ──> validate_research ──(invalid + budget)──> research
                    └─(ok)──> consolidate ──> gate ──(errors + budget)──> consolidate
                              (clean/dry)──> matrix ──> hiring ──> END

Research is a fan-out across every available provider; validate_research marks
each provider usable/unusable (>=150 usable rows) and surgical retry loops
re-run ONLY what failed, never the whole graph. Consolidation picks the best
Golden Record across the provider chain; the offline Level-3-style gate
quality.py judges it and can loop consolidation back up to MAX_RETRIES.

Every run persists a research bundle for offline demos; with no keys
configured the graph short-circuits to a clearly-labelled illustrative
fallback bundle with the same exit shape.
"""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypedDict

from app.intelligence import consolidation as cons
from app.intelligence import parsing, prompts, providers, quality
from app.intelligence.golden_record import column_for_id
from app.intelligence.store import (duration_ms, fallback_expectation_matrix, fallback_hiring,
                                    load_provider_research, load_research, now_iso,
                                    save_artifacts, save_provider_research, snapshot_files)

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
MIN_VALID_ROWS = 150
MAIN_PROVIDERS = ["openrouter", "groq", "gemini"]

try:  # LangGraph is pure Python; degrade to the equivalent sequential walk.
    from langgraph.graph import END, StateGraph
    HAS_LANGGRAPH = True
except ImportError:  # pragma: no cover
    StateGraph = END = None  # type: ignore
    HAS_LANGGRAPH = False


class GraphState(TypedDict, total=False):
    company: str
    providers: list[str]

    # research fan-out
    rows: dict[str, list]
    raw: dict[str, str]
    valid: dict[str, bool]
    attempts: dict[str, int]

    # consolidation + gate
    golden: dict[str, str]
    golden_gate: dict
    consolidator: str | None

    # secondary artifacts
    matrix: dict
    hiring: dict | None

    # bookkeeping
    stages: list
    exceptions: list
    log: list


def _log(state: dict, message: str) -> None:
    logs = state.setdefault("log", [])
    if isinstance(logs, list):
        logs.append(message)


def _stage(state: dict, name: str, start: float, detail: str | None = None, status: str = "ok") -> None:
    stages = state.setdefault("stages", [])
    if isinstance(stages, list):
        stages.append({"stage": name, "status": status, "duration_ms": duration_ms(start), "detail": detail})


def _load_company_data() -> dict:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(root_dir, "data", "talent_check_company_skillsets.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"source": "illustrative fallback", "companies": {}}


def availability() -> list[str]:
    return [p["provider"] for p in providers.provider_status() if p["available"]]


def _invoke_any(name: str, prompt: str) -> str:
    out = providers.call_provider(name, prompt, timeout=120)
    if not out.get("ok"):
        raise RuntimeError(out.get("error") or f"{name} unavailable")
    return out.get("text") or ""# ------------------------------------------------------------------ nodes ----
def _research_one(company: str, prompt: str, name: str, attempt: int) -> dict:
    """One provider leg of the research fan-out. Pure: returns its outcome,
    the caller merges into graph state so threads never mutate shared state."""
    start = time.time()
    outcome = providers.call_provider(name, prompt, timeout=90)
    if not outcome.get("ok"):
        return {"name": name, "attempt": attempt, "ok": False, "rows": [], "raw": "",
                "stage": (f"research fan-out ({name} attempt {attempt})",
                          "error", duration_ms(start), (outcome.get("error") or "unavailable")[:200]),
                "log": f"[research] {name} FAILED (attempt {attempt})"}
    text = outcome.get("text") or ""
    rows = parsing.parse_markdown_table(text)
    usable = sum(1 for r in rows if column_for_id(r.get("ID")))
    return {"name": name, "attempt": attempt, "ok": True, "rows": rows, "raw": text[:2000],
            "model": outcome.get("model", ""),
            "stage": (f"research fan-out ({name}{' · retry' if attempt > 1 else ''})",
                      "ok", duration_ms(start), f"{usable}/{len(rows)} rows mapped to schema ids"),
            "log": f"[research] {name}: {len(rows)} rows parsed (attempt {attempt})"}


def research_node(state: dict) -> dict:
    """CONCURRENT fan-out to every provider NOT yet marked valid
    (surgical re-entry: only failed legs are ever re-run)."""
    company = state["company"]
    prompt = prompts.research(company)
    targets = [p for p in state["providers"] if not state.get("valid", {}).get(p)]
    for name in targets:
        state.setdefault("attempts", {})[name] = state["attempts"].get(name, 0) + 1
    if not targets:
        return state

    legs = [(name, state["attempts"][name]) for name in targets]
    # Bound concurrency: each leg is a long LLM call; cap parallel upstream load.
    max_workers = min(len(legs), int(os.getenv("RESEARCH_MAX_WORKERS", "4")))
    if max_workers <= 1 or len(legs) == 1:
        results = [_research_one(company, prompt, name, n) for name, n in legs]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(lambda ln: _research_one(company, prompt, ln[0], ln[1]), legs))

    # Merge in submission order so stages/logs stay deterministic across runs.
    for res in results:
        name = res["name"]
        if res["ok"]:
            state.setdefault("rows", {})[name] = res["rows"]
            state.setdefault("raw", {})[name] = res["raw"]
            save_provider_research(company, name,
                                   {"provider": name, "model": res.get("model", ""), "rows": res["rows"]})
        else:
            state.setdefault("rows", {})[name] = []
        sname, status, dur, detail = res["stage"]
        state.setdefault("stages", []).append(
            {"stage": sname, "status": status, "duration_ms": dur, "detail": detail})
        _log(state, res["log"])
    return state


def validate_research_node(state: dict) -> dict:
    for p in state["providers"]:
        rows = (state.get("rows") or {}).get(p) or []
        usable = sum(1 for r in rows if column_for_id(r.get("ID")))
        state.setdefault("valid", {})[p] = usable >= MIN_VALID_ROWS
        _log(state, f"[validate] {p}: {usable} usable rows -> {'OK' if state['valid'][p] else 'RETRY'}")
    return state


def route_after_validate(state: dict) -> str:
    invalid = [p for p in state["providers"] if not state.get("valid", {}).get(p)]
    if not invalid:
        return "consolidate"
    can_retry = any(state.get("attempts", {}).get(p, 0) < MAX_RETRIES for p in invalid)
    return "research" if can_retry else "consolidate"


def consolidate_node(state: dict) -> dict:
    attempts = state.setdefault("attempts", {}).get("consolidate", 0) + 1
    state["attempts"]["consolidate"] = attempts
    start = time.time()
    sources = {p: rows for p in state["providers"] if (rows := (state.get("rows") or {}).get(p))}
    if not sources:  # reuse saved research from an earlier attempt (Level-4 load_research)
        for p in state["providers"]:
            saved = load_provider_research(state["company"], p)
            if saved:
                sources[p] = saved.get("rows") or []
    if not sources:
        state.setdefault("exceptions", []).append("consolidate: no research rows available")
        _stage(state, "consolidate (attempt failed)", start, "no research rows available", status="error")
        return state
    try:
        out = cons.consolidate(sources, _invoke_any, available=state["providers"])
        state["golden"] = out["record"]
        state["consolidator"] = out["provider"]
        _stage(state, f"consolidate{' · retry' if attempts > 1 else ''} ({out['provider']})", start,
               f"{out['usable']} usable parameters" + ("; " + "; ".join(
                   f"{a['provider']}: {a.get('usable')} usable" if 'usable' in a else f"{a['provider']}: {a.get('error','error')[:60]}"
                   for a in out["attempts"])))
        _log(state, f"[consolidate] {out['provider']}: {out['usable']} usable params")
    except Exception as exc:
        state.setdefault("exceptions", []).append(f"consolidate: {exc}"[:240])
        _stage(state, "consolidate (attempt failed)", start, str(exc)[:200], status="error")
    return state


def gate_node(state: dict) -> dict:
    diags = quality.validate_golden_record(state.get("golden") or {})
    state["golden_gate"] = quality.quality_verdict(diags)
    _log(state, f"[gate] golden record: {state['golden_gate']['errors']} error(s), "
                f"{state['golden_gate']['warnings']} warning(s)")
    return state


def route_after_gate(state: dict) -> str:
    errors = (state.get("golden_gate") or {}).get("errors", 0)
    if errors and state.get("attempts", {}).get("consolidate", 0) < MAX_RETRIES:
        _log(state, "[gate] retrying consolidation to fix data-quality errors")
        return "consolidate"
    return "matrix"


def matrix_node(state: dict) -> dict:
    """Expectation matrix (wide Level-Code row) from the consolidating provider."""
    company = state["company"]
    start = time.time()
    primary = state.get("consolidator") or state["providers"][0]
    try:
        outcome = providers.call_provider(primary, prompts.expectation_matrix(company), timeout=60)
        rows = parsing.parse_markdown_table(outcome.get("text") or "")
        matrix = quality.parse_matrix_row(rows[0] if rows else {})
        if not matrix["tokens"]:
            raise ValueError("no Level-Code tokens in output")
        state["matrix"] = matrix
        _stage(state, f"expectation matrix ({primary})", start, f"{len(matrix['tokens'])}/12 skills tokenised")
        _log(state, f"[matrix] {primary}: {len(matrix['tokens'])} skills")
    except Exception as exc:
        state["matrix"] = {"companies": company, "tokens": {}}
        state.setdefault("exceptions", []).append("expectation matrix: skipped, unparsable"[:200])
        _stage(state, "expectation matrix (failed)", start, str(exc)[:200], status="error")
    return state


def hiring_node(state: dict) -> dict:
    company = state["company"]
    start = time.time()
    primary = state.get("consolidator") or state["providers"][0]
    try:
        outcome = providers.call_provider(primary, prompts.hiring(company), timeout=60)
        hiring = parsing.extract_json(outcome.get("text") or "")
        if not isinstance(hiring, dict):
            raise ValueError("hiring output was not a JSON object")
        state["hiring"] = hiring
        _stage(state, f"hiring agent ({primary})", start,
               f"{len(hiring.get('job_role_details') or [])} role profile(s)")
        _log(state, "[hiring] validated + stored")
    except Exception as exc:
        state["hiring"] = None
        state.setdefault("exceptions", []).append("hiring rounds: skipped, unparsable"[:200])
        _stage(state, "hiring agent (failed)", start, str(exc)[:200], status="error")
    return state


def _build_graph():
    g = StateGraph(GraphState)
    g.add_node("research", research_node)
    g.add_node("validate_research", validate_research_node)
    g.add_node("consolidate", consolidate_node)
    g.add_node("gate", gate_node)
    g.add_node("matrix", matrix_node)
    g.add_node("hiring", hiring_node)

    g.set_entry_point("research")
    g.add_edge("research", "validate_research")
    g.add_conditional_edges("validate_research", route_after_validate,
                            {"research": "research", "consolidate": "consolidate"})
    g.add_edge("consolidate", "gate")
    g.add_conditional_edges("gate", route_after_gate,
                            {"consolidate": "consolidate", "matrix": "matrix"})
    g.add_edge("matrix", "hiring")
    g.add_edge("hiring", END)
    return g.compile()


_COMPILED = _build_graph() if HAS_LANGGRAPH else None


# ------------------------------------------------------- offline fallback ----

SKILL_METADATA = {
    "coding": {"code": "COD", "name": "Coding", "topics": ["Clean Code", "Language Idioms", "Edge Cases", "Debugging"]},
    "data_structures_and_algorithms": {"code": "DSA", "name": "Data Structures & Algorithms", "topics": ["Arrays & Strings", "Trees & Graphs", "Dynamic Programming", "Time/Space Complexity"]},
    "object_oriented_programming_and_design": {"code": "OOD", "name": "Object-Oriented Design", "topics": ["Design Patterns", "SOLID Principles", "Class Modelling", "Encapsulation"]},
    "aptitude_and_problem_solving": {"code": "APTI", "name": "Aptitude & Problem Solving", "topics": ["Logical Reasoning", "Quantitative Analysis", "Puzzles", "Critical Thinking"]},
    "communication_skills": {"code": "COMM", "name": "Communication", "topics": ["Technical Articulation", "Cross-functional Collaboration", "Interview Presence"]},
    "ai_native_engineering": {"code": "AI", "name": "AI/ML Engineering", "topics": ["Machine Learning Fundamentals", "LLM APIs & Prompting", "Model Evaluation"]},
    "devops_and_cloud": {"code": "CLOUD", "name": "DevOps & Cloud", "topics": ["Containers (Docker)", "CI/CD Pipelines", "AWS/Cloud Basics", "Infrastructure"]},
    "sql_and_design": {"code": "SQL", "name": "SQL & Data Modelling", "topics": ["Complex Queries & Joins", "Schema Normalization", "Indexing & Performance"]},
    "software_engineering": {"code": "SWE", "name": "Software Engineering", "topics": ["Git & Version Control", "Testing & QA", "API Design (REST/gRPC)", "Agile Lifecycle"]},
    "system_design_and_architecture": {"code": "SYSD", "name": "System Design & Architecture", "topics": ["High Availability", "Microservices", "Caching & Queues", "Scalability"]},
    "computer_networking": {"code": "NETW", "name": "Computer Networking", "topics": ["TCP/IP & OSI", "HTTP/HTTPS & DNS", "Sockets", "Network Security"]},
    "operating_system": {"code": "OS", "name": "Operating Systems", "topics": ["Process & Threading", "Memory Management", "Concurrency & Locks", "Linux Shell & File Systems"]},
}


def _synthesize_artifacts(company: str, golden: dict, matrix: dict, hiring: dict | None, providers_used: list[str]) -> dict:
    tokens = matrix.get("tokens", {}) if isinstance(matrix, dict) else {}
    skills = []
    for col in quality.SKILL_COLUMNS:
        meta = SKILL_METADATA.get(col, {"code": col[:4].upper(), "name": col.replace("_", " ").title(), "topics": []})
        t = tokens.get(col, {"level": 5, "bloom_code": "AP"})
        level = int(t.get("level") or 5)
        bloom = t.get("bloom_code") or "AP"
        skills.append({
            "skill_set_code": meta["code"],
            "skill_name": meta["name"],
            "required_level": level,
            "bloom_code": bloom,
            "rationale": f"Hiring bar expectation for {company} campus engineering candidates.",
            "typical_topics": meta["topics"],
            "confidence": "high" if (providers_used and not t.get("generic")) else "low",
            "source_agreement": f"{len(providers_used)}/{len(providers_used)} sources" if providers_used else "0/0 (offline heuristics)",
            "level_spread": 0,
        })

    skill_matrix = {
        "company_name": company,
        "skills": skills,
        "consensus_sources": len(providers_used),
        "conflicts": [],
    }

    normalized_hiring = hiring if isinstance(hiring, dict) else {}
    raw_roles = normalized_hiring.get("job_role_details") or normalized_hiring.get("job_roles") or []
    canonical_role_details = []
    frontend_job_roles = []

    for role in raw_roles:
        r_title = role.get("role_title") or "Software Engineer"
        r_cat = role.get("role_category") or "SDE"
        r_opp = role.get("opportunity_type") or "Employment"
        r_desc = role.get("job_description") or role.get("job_summary") or f"Campus engineering opportunities at {company}."
        rounds_list = []
        for r in role.get("hiring_rounds", []):
            tested = [s["skill_set_code"] for s in r.get("skill_sets", []) if isinstance(s, dict) and "skill_set_code" in s]
            if not tested and r.get("skills_tested"):
                tested = r["skills_tested"]
            questions = [s["typical_questions"] for s in r.get("skill_sets", []) if isinstance(s, dict) and "typical_questions" in s]
            if not questions and r.get("typical_questions"):
                questions = r["typical_questions"] if isinstance(r["typical_questions"], list) else [r["typical_questions"]]
            rounds_list.append({
                "round_number": r.get("round_number", 1),
                "round_name": r.get("round_name", "Interview"),
                "round_category": r.get("round_category", "Interview"),
                "evaluation_type": r.get("evaluation_type", "Technical"),
                "assessment_mode": r.get("assessment_mode", "Online"),
                "duration_minutes": r.get("duration_minutes", 60),
                "skill_sets": r.get("skill_sets") or [{"skill_set_code": c, "typical_questions": "Standard technical interview assessment."} for c in (tested or ["COD", "DSA"])],
                "skills_tested": tested or ["COD", "DSA"],
                "typical_questions": questions or ["Solve core technical challenges and discuss problem approaches."],
            })
        canonical_role_details.append({
            "opportunity_type": r_opp,
            "role_title": r_title,
            "role_category": r_cat,
            "job_description": r_desc,
            "compensation": role.get("compensation") or "CTC",
            "ctc_or_stipend": role.get("ctc_or_stipend") or 0,
            "bonus": role.get("bonus") or "NA",
            "benefits_summary": role.get("benefits_summary") or "Comprehensive company benefits.",
            "hiring_rounds": rounds_list,
        })
        frontend_job_roles.append({
            "role_title": r_title,
            "role_category": r_cat,
            "opportunity_type": r_opp,
            "job_summary": r_desc,
            "hiring_rounds": rounds_list,
        })

    enriched_hiring = {
        "company_name": company,
        "job_role_details": canonical_role_details,
        "job_roles": frontend_job_roles,
    }

    company_brief = {
        "company_name": company,
        "about": golden.get("Company Description") or golden.get("Overview") or (
            f"Verified multi-agent research profile for {company}." if providers_used else
            f"Bundled offline snapshot derived from illustrative expectations for {company}."
        ),
        "campus_program": golden.get("Campus Hiring Program") or "Graduate Campus Recruitment Program",
        "interview_style": golden.get("Interview Culture") or "Problem-solving, algorithmic design, and core engineering depth",
        "prep_focus": [
            f"Focus on {skills[0]['skill_name']} and {skills[1]['skill_name'] if len(skills) > 1 else 'DSA'}",
            "Practice problem breakdown and articulating algorithmic tradeoffs",
            "Demonstrate clean architectural code and edge-case handling"
        ]
    }

    return {
        "golden_record": golden,
        "expectation_matrix": matrix,
        "skill_matrix": skill_matrix,
        "hiring_rounds": enriched_hiring,
        "company_brief": company_brief,
    }


def _offline_bundle(company: str, stages: list, notice: str) -> dict:
    bundled = snapshot_files()
    matrix = bundled.get("expectation_matrix") or fallback_expectation_matrix(company, _load_company_data())
    hiring = bundled.get("hiring_rounds") or fallback_hiring(company, _load_company_data())
    diags = quality.validate_expectation_matrix(matrix) + quality.validate_hiring_rounds(hiring)
    if stages is not list:
        stages = list(stages)
    stages.append({"stage": "research (offline fallback)", "status": "ok", "duration_ms": 0,
                   "detail": "No LLM keys configured; bundled illustrative snapshot used"})
    artifacts = _synthesize_artifacts(company, {}, matrix, hiring, [])
    return {
        "company": company, "researched_at": now_iso(), "stages": stages,
        "mode": "offline-fallback", "verified": False, "notice": notice,
        "providers_used": [], "langgraph": HAS_LANGGRAPH,
        "artifacts": artifacts,
        "quality": quality.quality_verdict(diags),
        "quality_report_md": quality.build_quality_report(company, diags),
    }


def _fallback_tail(state: dict, company: str, reason: str) -> dict:
    stages = list(state.get("stages") or [])
    stages.append({"stage": "pipeline error", "status": "error", "duration_ms": 0, "detail": reason[:200]})
    bundle = _offline_bundle(company, stages,
                             "Research failed mid-pipeline; an offline illustrative snapshot was used. Verified data was NOT produced.")
    save_artifacts(company, bundle)
    return bundle


# ------------------------------------------------------------- sequential ----

def _run_sequential(state: dict) -> None:
    """LangGraph-free walk executing the same nodes/loops (bounded)."""
    research_node(state)
    for _ in range(MAX_RETRIES + 1):
        validate_research_node(state)
        if route_after_validate(state) == "consolidate":
            break
        research_node(state)
    for _ in range(MAX_RETRIES + 1):
        consolidate_node(state)
        gate_node(state)
        if route_after_gate(state) != "consolidate":
            break
    matrix_node(state)
    hiring_node(state)


# ------------------------------------------------------------------ entry ----

def run_pipeline(company: str, requested_providers: list[str] | None = None) -> dict:
    """Run the intelligence pipeline for one company.
    
    SUPABASE-FIRST RESOLUTION:
    If the company exists in the team's verified 118-company Supabase database,
    instantly load its verified 163-parameter corporate profile and 12-skill
    Bloom taxonomy levels without wasting any LLM tokens.
    
    If NOT in Supabase (e.g. unlisted startup or custom company), invoke the
    multi-agent LLM consensus graph across Groq, OpenRouter, and Gemini.
    """
    company = company.strip()[:80]

    # 1. Check team Supabase database first
    from app.intelligence import supabase_source
    sb_bundle = supabase_source.build_bundle_from_supabase(company)
    if sb_bundle:
        save_artifacts(company, sb_bundle)
        return sb_bundle

    available = set(availability())
    wanted = requested_providers or MAIN_PROVIDERS
    providers_list = [p for p in wanted if p in available]

    if not providers_list:
        bundle = _offline_bundle(company, [],
                                 "This company has NOT been researched by LLM agents. Add provider keys and re-run for verified data.")
        save_artifacts(company, bundle)
        return bundle

    state: dict = {
        "company": company, "providers": providers_list,
        "rows": {}, "raw": {}, "valid": {}, "attempts": {},
        "golden": {}, "golden_gate": {}, "consolidator": None,
        "matrix": {}, "hiring": None,
        "stages": [], "exceptions": [], "log": [],
    }

    start = time.time()
    if _COMPILED is not None:
        try:
            result = _COMPILED.invoke(state)
            state = dict(result) if isinstance(result, dict) else state
        except Exception as exc:  # graph-level blow-up must not crash the API
            state.setdefault("exceptions", []).append(f"graph: {exc}"[:240])
            return _fallback_tail(state, company, str(exc))
    else:
        _run_sequential(state)

    elapsed = duration_ms(start)
    state.setdefault("stages", []).append({
        "stage": f"langgraph pipeline ({' + '.join(providers_list)})", "status": "ok",
        "duration_ms": elapsed, "detail": f"{len(state.get('log', []))} node transitions",
    })
    return _bundle(state)


def _bundle(state: dict) -> dict:
    company = state["company"]
    golden = state.get("golden") or {}
    matrix = state.get("matrix") or {"companies": company, "tokens": {}}
    hiring = state.get("hiring")

    diags: list = []
    if golden:
        diags += quality.validate_golden_record(golden)
    diags += quality.validate_expectation_matrix(matrix)
    if hiring:
        diags += quality.validate_hiring_rounds(hiring)
    verdict = quality.quality_verdict(diags)

    used = [p for p in state.get("providers", []) if state.get("valid", {}).get(p)] or list(state.get("providers", []))
    artifacts = _synthesize_artifacts(company, golden, matrix, hiring, used)
    bundle = {
        "company": company,
        "researched_at": now_iso(),
        "stages": state.get("stages", []),
        "mode": "llm-research",
        "verified": verdict["passed"],
        "notice": "",
        "providers_used": used,
        "langgraph": HAS_LANGGRAPH,
        "artifacts": artifacts,
        "quality": verdict,
        "quality_report_md": quality.build_quality_report(company, diags),
    }
    save_artifacts(company, bundle)
    return bundle


def provider_status_and_functions(requested: list[str] | None = None):
    names = requested or MAIN_PROVIDERS
    info = providers.provider_status()
    return [p for p in info if p["provider"] in names] or info


def get_or_none(company: str) -> dict | None:
    return load_research(company)


def snapshots() -> dict:
    return snapshot_files()
