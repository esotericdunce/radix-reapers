"""Company Intelligence: research → consensus → quality gates → verified skill data.

Differentiator layer for RADIX TalentMatch. Mirrors the OpenRadix Level-4/5
agentic pipeline (multi-LLM research fan-out, consensus consolidation, a
Level-3-style offline validation gate, and surgical stage retry), but it is
vendored into the product itself and runs over lightweight REST providers.
No LangChain dependency; no keys required (falls back to bundled snapshot).
"""
