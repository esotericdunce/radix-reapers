"""Raw LLM text -> structured data (ported from Level 4 `parsing.py`).

* `parse_markdown_table(text)` — the first GitHub-style table in the text,
  as a list of dicts keyed by header (research outputs / consolidated
  golden-record tables / expectation-matrix rows).
* `extract_json(text)` — survives ```json fences and prose around a JSON
  object (hiring rounds, skill matrices).

Pure standard library — fully unit-testable offline.
"""
from __future__ import annotations

import json
import re
from typing import Any


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    body = line.replace("|", "").replace(":", "").replace("-", "").strip()
    return body == ""


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    """Parse the first GitHub-style markdown table found in `text`."""
    rows = [ln for ln in (text or "").splitlines() if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []
    headers = _cells(rows[0])
    headers = [h for i, h in enumerate(headers) if not (i == 0 and h == "")] or headers
    out: list[dict[str, str]] = []
    for line in rows[1:]:
        if _is_separator(line):
            continue
        values = _cells(line)
        if len(values) < len(headers):
            values += [""] * (len(headers) - len(values))
        out.append({h: values[i] for i, h in enumerate(headers)})
    return out


def extract_json(text: str) -> dict[str, Any]:
    """Pull the first balanced JSON object out of arbitrary LLM text."""
    if not text or not isinstance(text, str):
        raise ValueError("Empty model response")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(line for line in cleaned.splitlines()
                            if not line.strip().startswith("```"))
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(cleaned)):
            ch = cleaned[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start:i + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict):
                            return parsed
                    except ValueError:
                        break
                    break
        start = cleaned.find("{", start + 1)
    raise ValueError("No valid JSON object found in model response")
