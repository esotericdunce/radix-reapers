"""Small explicit aliases for genuinely equivalent skill names."""
import re


def normalize(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


ALIASES = {
    "dsa": "Data Structures and Algorithms",
    "datastructuresandalgorithms": "Data Structures and Algorithms",
    "oop": "Object-Oriented Programming",
    "objectorientedprogramming": "Object-Oriented Programming",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ml": "Machine Learning",
    "machinelearning": "Machine Learning",
}


def canonical_name(name: str) -> str:
    clean = name.strip()
    exact = ALIASES.get(normalize(clean))
    if exact:
        return exact
    # Typo-tolerant aliasing via rapidfuzz: "D.S.A.", "Data Structure & Algo", …
    fuzzy = _fuzzy_alias(clean)
    return fuzzy if fuzzy else clean


def _fuzzy_alias(name: str, floor: int = 92) -> str | None:
    try:
        from rapidfuzz import fuzz, process
    except ImportError:  # optional dependency — exact aliases still work
        return None
    key = normalize(name)
    if not key:
        return None
    hit = process.extractOne(key, list(ALIASES), scorer=fuzz.ratio)
    if hit and hit[1] >= floor:
        return ALIASES[hit[0]]
    return None


def canonical_key(name: str) -> str:
    return normalize(canonical_name(name))
