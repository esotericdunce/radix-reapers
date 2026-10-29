"""Level-4-style consolidation agent.

Builds the ~489-row dataset from the research fan-out and asks one LLM to
consolidate it into a single Golden Record (zero-fabrication: it must *select*
existing candidate rows, never invent). The result is mapped back to a
`{parameter_name: value}` record via the 163-parameter schema.

Provider chain mirrors Level 5: `CONSOLIDATION_PROVIDERS` env (default
`gemini,groq,openrouter` — huge context first), falling through on hard errors
or unusable tables while keeping the best partial result. The offline gate
(quality.py) then judges the record.
"""
from __future__ import annotations

import os
from typing import Any

from app.intelligence import parsing, prompts
from app.intelligence.golden_record import COLUMNS, column_for_id

_HEADERS = "| ID | Category | A/C | Parameter | Research Output / Data | Source |"
_SEP = "|---|---|---|---|---|---|"


def consolidation_providers() -> list[str]:
    raw = os.getenv("CONSOLIDATION_PROVIDERS", "gemini,groq,openrouter")
    return [p.strip() for p in raw.split(",") if p.strip()]


def build_dataset(per_provider_rows: dict[str, list[dict[str, str]]]) -> str:
    """Render every provider's research rows into the merge-prompt dataset."""
    lines = [_HEADERS, _SEP]
    for source, rows in per_provider_rows.items():
        for r in rows:
            lines.append(
                f"| {r.get('ID', '')} | {r.get('Category', '')} | {r.get('A/C', '')} "
                f"| {r.get('Parameter', '')} | {r.get('Research Output / Data', '')} | {source} |"
            )
    return "\n".join(lines)


def record_from_table(rows: list[dict[str, str]]) -> dict[str, str]:
    """Map consolidated rows (ID -> parameter name -> value)."""
    record: dict[str, str] = {}
    for r in rows:
        col = column_for_id(r.get("ID"))
        if col:
            value = (r.get("Research Output / Data") or "").strip()
            if value:
                record.setdefault(col, value)
    return record


def usable_count(record: dict[str, str]) -> int:
    return sum(1 for c in COLUMNS if (record.get(c) or "").strip())


def consolidate(
    per_provider_rows: dict[str, list[dict[str, str]]],
    invoke_provider: Any,
    available: list[str] | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Run consolidation across the provider chain; keep the best partial.

    `invoke_provider(name, prompt) -> str` comes from the orchestrator so the
    LangGraph layer decides retries; here we only walk the chain.

    Returns {record, provider, usable, attempts: [{provider, error|usable}]}.
    Raises ValueError when no provider yields a parsable table.
    """
    chain = provider_chain(consolidation_providers(), available or [])
    if not chain:
        raise ValueError("No configured consolidation provider is available")

    dataset = build_dataset(per_provider_rows)
    if max_rows is not None:
        lines = dataset.splitlines()
        dataset = "\n".join(lines[: max_rows * (len(per_provider_rows) + 2) + 2])

    prompt = prompts.consolidation(dataset)
    attempts: list[dict[str, Any]] = []
    best: dict[str, str] = {}
    best_usable = -1
    best_provider = None

    for name in chain:
        try:
            text = invoke_provider(name, prompt)
            candidate = record_from_table(parsing.parse_markdown_table(text))
        except Exception as exc:  # hard error or unparsable text
            attempts.append({"provider": name, "error": f"{getattr(exc, '__class__', type(exc)).__name__}: {exc}"[:200]})
            continue
        usable = usable_count(candidate)
        attempts.append({"provider": name, "usable": usable})
        if usable > best_usable:
            best_usable, best, best_provider = usable, candidate, name
        if usable >= 150:  # Level-5 MIN_VALID_ROWS: good enough, stop the chain
            break

    if best_usable < 1:  # a table with zero mapped parameters is not consolidation
        raise ValueError("No consolidation provider returned a parsable table")
    return {"record": best, "provider": best_provider, "usable": best_usable, "attempts": attempts}


def provider_chain(configured: list[str], available: list[str]) -> list[str]:
    avail = set(available)
    chain = [p for p in configured if not avail or p in avail]
    return chain or []
