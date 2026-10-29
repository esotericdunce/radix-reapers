r"""Offline data-quality gate for the Golden Record pipeline (Level-3 heritage).

The rule registry is the Level-3 rules library shape-checked against every
artifact the pipeline produces — now over the canonical 163-parameter record:

* Golden record  – presence, atomic/composite delimiter rules, placeholder and
                   hygiene rules (ported from Level 3 `rules.py` semantics),
                   plus targeted URL / rating shapes.
* Expectation    – the wide `Level-Code` row (12 skills, `^\d{1,2}-(CU|AP|AS|EV|CR)$`).
  matrix
* Hiring rounds  – envelope shape per the canonical hiring JSON contract.

(The docstring is a raw string: it quotes regex shapes.)

Each rule returns a list of diagnostics; `quality_verdict` aggregates them into
a PASS/FAIL verdict, and `build_quality_report` renders the markdown report.
"""
from __future__ import annotations

import re
from typing import Any

from app.intelligence.golden_record import (BY_NAME, COLUMNS, PLACEHOLDERS, RATING_PARAMS,
                                            URL_PARAMS, is_blank, split_elements)

BLOOM_CODES = {"CU", "AP", "AS", "EV", "CR"}
LEVEL_CODE_RE = re.compile(r"^(\d{1,2})-(CU|AP|AS|EV|CR)$")
SKILL_COLUMNS = [
    "coding", "data_structures_and_algorithms", "object_oriented_programming_and_design",
    "aptitude_and_problem_solving", "communication_skills", "ai_native_engineering",
    "devops_and_cloud", "sql_and_design", "software_engineering",
    "system_design_and_architecture", "computer_networking", "operating_system",
]
SKILL_CODES = ["DSA", "COD", "OOD", "APTI", "COMM", "AI", "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS"]

ROUND_CATEGORIES = {"Coding Test", "Interview"}
EVALUATION_TYPES = {"Technical", "HR"}
ASSESSMENT_MODES = {"Online", "Onsite"}

_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
_BULLET_RE = re.compile(r"(^|\s)[•\-\*]\s|\d+\.\s")
_MAX_ELEMENT_LEN = 300


def _diag(artifact, path, message, severity="error", rule="", scope="Per-Parameter", category="validity"):
    return {"artifact": artifact, "path": path, "message": message, "severity": severity,
            "rule": rule, "scope": scope, "category": category}


# ------------------------------------------------------------------ rules ----

def rule_presence(name, value):
    """Level 4: never blank — blank is an error, explicit 'Not Found' is a warn."""
    if is_blank(value):
        return [_diag("golden_record", name, "value is blank (research must never leave a field empty)", rule="presence")]
    low = str(value).strip().lower()
    if low in PLACEHOLDERS:
        return [_diag("golden_record", name, f"placeholder value: {value!r} — verify before publishing",
                      severity="warn", rule="no_placeholder", category="plausibility")]
    return []


def rule_atomic(name, value):
    p = BY_NAME.get(name)
    if is_blank(value) or p is None or p.ac != "Atomic":
        return []
    if ";" in str(value):
        return [_diag("golden_record", name, "atomic field contains ';' (should be a single value)", rule="atomic_no_delimiter")]
    return []


def rule_composite(name, value):
    p = BY_NAME.get(name)
    if is_blank(value) or p is None or p.ac != "Composite":
        return []
    elements = split_elements(value)
    raw = str(value)
    out = []
    lo = p.minimum or 1
    hi = p.maximum
    if len(elements) < lo:
        out.append(_diag("golden_record", name, f"composite needs >= {lo} elements, got {len(elements)}", rule="composite_min_count"))
    if hi is not None and len(elements) > hi:
        out.append(_diag("golden_record", name, f"composite allows <= {hi} elements, got {len(elements)}", rule="composite_max_count"))
    if raw.rstrip().endswith(";"):
        out.append(_diag("golden_record", name, "trailing delimiter", severity="warn", rule="composite_no_trailing_delimiter", category="formatting"))
    if any(len(e) > _MAX_ELEMENT_LEN for e in elements):
        out.append(_diag("golden_record", name, f"composite element exceeds {_MAX_ELEMENT_LEN} chars",
                         severity="warn", rule="composite_max_element_length", category="formatting"))
    return out


def rule_hygiene(name, value):
    if is_blank(value):
        return []
    text = str(value)
    out = []
    if "\n" in text:
        out.append(_diag("golden_record", name, "contains a newline (cells must be single-line)",
                         severity="warn", rule="no_newlines", category="formatting"))
    if _BULLET_RE.search(text):
        out.append(_diag("golden_record", name, "contains a bullet/numbered-list marker",
                         severity="warn", rule="no_bullets", category="formatting"))
    if text != text.strip():
        out.append(_diag("golden_record", name, "has leading/trailing whitespace",
                         severity="warn", rule="no_leading_trailing_space", category="formatting"))
    if "  " in text:
        out.append(_diag("golden_record", name, "contains a double space",
                         severity="warn", rule="no_double_space", category="formatting"))
    if not re.search(r"[A-Za-z0-9]", text):
        out.append(_diag("golden_record", name, "value has no alphanumeric content", rule="not_only_punctuation"))
    return out


def rule_url_shape(name, value):
    if name not in URL_PARAMS or is_blank(value):
        return []
    for v in split_elements(value) or [str(value)]:
        if not _URL_RE.match(v):
            return [_diag("golden_record", name, f"not a valid URL: {v!r}", severity="warn", rule="url_shape", category="formatting")]
    return []


def rule_rating_shape(name, value):
    if name not in RATING_PARAMS or is_blank(value):
        return []
    m = re.search(r"\d+(\.\d+)?", str(value))
    if not m:
        return [_diag("golden_record", name, f"no numeric rating: {value!r}", severity="warn", rule="rating_range_0_10", category="plausibility")]
    num = float(m.group())
    if not 0 <= num <= 10:
        return [_diag("golden_record", name, f"rating {num} out of range 0-10", severity="warn", rule="rating_range_0_10", category="plausibility")]
    return []


def rule_all_present(record):
    missing = [c for c in COLUMNS if c not in record]
    if missing:
        return [_diag("golden_record", "GLOBAL",
                      f"{len(missing)} parameters missing keys: {missing[:5]}...",
                      rule="all_163_present", scope="Global", category="completeness")]
    return []


# ---------------------------------------------------------- gate: record ----

def validate_golden_record(record: dict[str, Any]) -> list[dict]:
    if not isinstance(record, dict) or not record:
        return [_diag("golden_record", "/", "golden record must be a non-empty {parameter: value} map",
                      rule="shape", scope="Global", category="shape")]
    unknown = [k for k in record if k not in BY_NAME]
    diags: list[dict] = []
    if unknown:
        diags.append(_diag("golden_record", "GLOBAL", f"unexpected keys in record: {unknown[:5]}...",
                           severity="warn", rule="no_unexpected_keys", scope="Global", category="completeness"))
    diags += rule_all_present(record)
    for name in COLUMNS:
        value = record.get(name, "")
        diags += rule_presence(name, value)
        diags += rule_atomic(name, value)
        diags += rule_composite(name, value)
        diags += rule_hygiene(name, value)
        diags += rule_url_shape(name, value)
        diags += rule_rating_shape(name, value)
    return diags


# ------------------------------------------------------ gate: matrix row ----

def parse_matrix_row(raw_row: dict[str, str] | None) -> dict[str, Any]:
    """Turn the canonical wide `companies|coding|...` row into tokens."""
    if not isinstance(raw_row, dict):
        return {"companies": "", "tokens": {}}
    companies = (raw_row.get("companies") or "").strip()
    tokens = {}
    for col in SKILL_COLUMNS:
        cell = (raw_row.get(col) or "").strip()
        m = LEVEL_CODE_RE.match(cell) if cell else None
        if m:
            tokens[col] = {"level": int(m.group(1)), "bloom_code": m.group(2), "raw": cell}
        elif cell:
            tokens[col] = {"level": None, "bloom_code": None, "raw": cell, "invalid": True}
    return {"companies": companies, "tokens": tokens}


def validate_expectation_matrix(matrix: dict[str, Any]) -> list[dict]:
    tokens = (matrix.get("tokens") or {}) if isinstance(matrix, dict) else {}
    if not tokens:
        return [_diag("expectation_matrix", "/", "expectation matrix must contain Level-Code tokens for the 12 skills",
                      rule="matrix_present", scope="Specific-Artifact", category="completeness")]
    diags: list[dict] = []
    invalid = [c for c, t in tokens.items() if t.get("invalid")]
    if invalid:
        diags.append(_diag("expectation_matrix", "/".join(invalid[:3]),
                           f"cells are not Level-Code tokens: {', '.join(invalid)}",
                           rule="level_code_valid", scope="Specific-Artifact", category="validity"))
    levels = [t["level"] for t in tokens.values() if isinstance(t.get("level"), int)]
    for col, t in tokens.items():
        if isinstance(t.get("level"), int) and not 1 <= t["level"] <= 10:
            diags.append(_diag("expectation_matrix", col, f"level {t['level']} out of range 1-10",
                               rule="level_in_range", scope="Specific-Artifact", category="range"))
    if levels and len(set(levels)) == 1 and len(tokens) == len(SKILL_COLUMNS):
        diags.append(_diag("expectation_matrix", "/", f"all {len(levels)} levels identical — the data looks unexamined; regenerate for a real bar",
                           severity="warn", rule="matrix_not_flat", scope="Specific-Artifact", category="plausibility"))
    return diags


# --------------------------------------------------------- gate: hiring ----

def _round_diag(path, round_name, message, rule):
    return _diag("hiring_rounds", f"{path}/{round_name}", message, rule=rule)


def _question_tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [p.strip() for p in value.split(";") if p.strip()]
    return []


def validate_hiring_rounds(hiring: dict[str, Any]) -> list[dict]:
    if not isinstance(hiring, dict) or not isinstance(hiring.get("job_role_details"), list) or not hiring.get("job_role_details"):
        return [_diag("hiring_rounds", "/", "hiring_rounds must be an object with a non-empty job_role_details array",
                      rule="shape", scope="Specific-Artifact", category="shape")]
    diags: list[dict] = []
    for ri, role in enumerate(hiring["job_role_details"]):
        if not isinstance(role, dict):
            diags.append(_diag("hiring_rounds", f"job_role_details/{ri}", "role must be an object", rule="shape", scope="Per-Role"))
            continue
        path = role.get("role_title") or f"job_role_details/{ri}"
        if str(role.get("opportunity_type") or "").strip() not in {"Employment", "Internship"}:
            diags.append(_diag("hiring_rounds", path, f"opportunity_type {role.get('opportunity_type')!r} is not allowed",
                               rule="opportunity_type_valid", scope="Per-Role"))
        rounds = role.get("hiring_rounds")
        if not isinstance(rounds, list) or not 3 <= len(rounds) <= 5:
            diags.append(_diag("hiring_rounds", path, f"a role must have 3-5 hiring rounds, got {len(rounds) if isinstance(rounds, list) else 'invalid'}",
                               rule="rounds_shape", scope="Per-Role"))
        numbers = [r.get("round_number") for r in rounds if isinstance(r, dict)] if isinstance(rounds, list) else []
        if numbers and numbers != sorted(numbers):
            diags.append(_diag("hiring_rounds", path, "round_number must be ascending", severity="warn",
                               rule="round_order", scope="Per-Role", category="formatting"))
        for r in rounds if isinstance(rounds, list) else []:
            if not isinstance(r, dict):
                continue
            name = r.get("round_name") or "?"
            if str(r.get("round_category") or "").strip() not in ROUND_CATEGORIES:
                diags.append(_round_diag(path, name, f"round_category {r.get('round_category')!r} is not allowed", "round_category_valid"))
            if str(r.get("evaluation_type") or "").strip() not in EVALUATION_TYPES:
                diags.append(_round_diag(path, name, f"evaluation_type {r.get('evaluation_type')!r} is not allowed", "evaluation_type_valid"))
            if str(r.get("assessment_mode") or "").strip() not in ASSESSMENT_MODES:
                diags.append(_round_diag(path, name, f"assessment_mode {r.get('assessment_mode')!r} is not allowed", "assessment_mode_valid"))
            skills = r.get("skill_sets")
            if not isinstance(skills, list) or not skills:
                diags.append(_round_diag(path, name, "skill_sets must be a non-empty list", "skill_sets_present"))
            else:
                for s in skills:
                    code = s.get("skill_set_code") if isinstance(s, dict) else None
                    if not isinstance(code, str) or not code.strip():
                        diags.append(_round_diag(path, name, f"invalid skill_set_code: {code!r}", "skill_code_valid"))
                    elif code.strip() not in SKILL_CODES:
                        diags.append(_round_diag(path, name, f"skill_set_code {code!r} is not one of the 12 catalog codes", "skill_code_valid"))
                    qs = _question_tokens(s.get("typical_questions")) if isinstance(s, dict) else []
                    if not qs:
                        diags.append(_round_diag(path, name, "typical_questions is empty", severity="warn",
                                                 rule="questions_present", scope="Per-Round", category="completeness"))
    return diags


# ----------------------------------------------------------------- report ----

def quality_verdict(diags: list[dict]) -> dict:
    errors = [d for d in diags if d["severity"] == "error"]
    warnings = [d for d in diags if d["severity"] == "warn"]
    return {"passed": not errors, "errors": len(errors), "warnings": len(warnings), "diagnostics": diags}


def build_quality_report(company, diags: list[dict]) -> str:
    verdict = quality_verdict(diags)
    lines = [f"# Data quality report — {company}", "",
             f"Verdict: **{'PASS' if verdict['passed'] else 'FAIL'}** · "
             f"{verdict['errors']} error(s), {verdict['warnings']} warning(s) "
             f"from the offline Level-3-style gate.", ""]
    if not diags:
        lines.append("No diagnostics. All rules reported clean.")
    else:
        for severity in ("error", "warn"):
            subset = [d for d in diags if d["severity"] == severity]
            if subset:
                lines.append(f"## {severity.capitalize()}s ({len(subset)})")
                by_artifact: dict[str, list[dict]] = {}
                for d in subset:
                    by_artifact.setdefault(d["artifact"], []).append(d)
                for artifact, group in by_artifact.items():
                    lines.append(f"### {artifact} ({len(group)})")
                    for d in group[:40]:
                        lines.append(f"- **[{d['artifact']}/{d['path']}] {d['rule']}** — {d['message']}")
                    if len(group) > 40:
                        lines.append(f"- …and {len(group) - 40} more")
                    lines.append("")
    return "\n".join(lines)
