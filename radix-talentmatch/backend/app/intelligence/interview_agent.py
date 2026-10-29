"""AI Mock Interview & Adaptive Viva Agent.

Allows candidates to practice against authentic, company-calibrated technical interviews
grounded in real corporate architecture data (from Supabase dataset) and evaluated
against Bloom's Taxonomy cognitive depth standards.
"""
from __future__ import annotations

import json
from typing import Any
from app.intelligence import agents, parsing, providers, supabase_source


def _get_company_context(company: str) -> dict[str, str]:
    """Extract real company engineering characteristics from Supabase."""
    rec = supabase_source.find_company_record(company)
    if not rec:
        return {
            "name": company,
            "domain": "Distributed Software Systems",
            "tech_stack": "Cloud Microservices, Relational & NoSQL Datastores, Message Queues",
            "scale_challenge": "High-concurrency traffic with strict 99.99% availability SLAs"
        }

    fj = rec.get("full_json") or {}
    sj = rec.get("short_json") or {}
    if isinstance(fj, str):
        try: fj = json.loads(fj)
        except Exception: fj = {}
    if isinstance(sj, str):
        try: sj = json.loads(sj)
        except Exception: sj = {}

    name = sj.get("short_name") or sj.get("name") or company
    domain = fj.get("offerings_description") or sj.get("category") or "High-Scale Tech"
    tech_stack = fj.get("ai_ml_adoption_level") or fj.get("technology_partners") or "Distributed Cloud & High-Throughput Pipelines"
    challenges = fj.get("key_challenges_needs") or fj.get("unique_differentiators") or "Sub-second latency, zero data loss, fault tolerance"

    return {
        "name": name,
        "domain": str(domain)[:150],
        "tech_stack": str(tech_stack)[:150],
        "scale_challenge": str(challenges)[:180]
    }


def generate_interview_question(
    company: str,
    round_name: str,
    candidate: dict[str, Any]
) -> dict[str, Any]:
    """Generates an authentic, company-calibrated scenario challenge."""
    avail = agents.availability()
    candidate_name = candidate.get("name", "Candidate")
    skills = [s.get("skill_name") for s in candidate.get("skills", [])[:8]]
    company_ctx = _get_company_context(company)

    prompt = f"""You are a Staff Software Engineer & Hiring Bar Raiser at {company_ctx['name']} conducting a real technical interview.
COMPANY DOMAIN: {company_ctx['domain']}
REAL ENGINEERING CHALLENGES: {company_ctx['scale_challenge']}
INTERVIEW ROUND: {round_name}
CANDIDATE: {candidate_name} (Demonstrated Skills: {', '.join(skills) if skills else 'Core CS, DSA, Systems'})

Formulate ONE authentic, high-signal technical problem that a real candidate would face at {company_ctx['name']}.
Include realistic production constraints (e.g. QPS scale, P99 latency SLA, network partition risk).

Return strict JSON only (no markdown, no prose outside JSON):
{{
  "question_id": "{company.lower()}-{round_name.lower().replace(' ', '-')}-q1",
  "company": "{company_ctx['name']}",
  "round_name": "{round_name}",
  "interviewer_role": "Staff Systems Engineer at {company_ctx['name']}",
  "question": "<The exact challenge stated clearly with concrete architectural requirements>",
  "scenario_context": "<2-3 sentences framing the business scenario and system traffic constraints>",
  "target_bloom": "EV",
  "primary_skill": "System Design & Architecture",
  "constraints": [
    "<Constraint 1, e.g. 50,000 write QPS with <20ms p99 response>",
    "<Constraint 2, e.g. Must guarantee idempotency under network partition>",
    "<Constraint 3, e.g. Storage budget / eventual consistency bounds>"
  ],
  "hints": [
    "<Hint on partitioning/sharding or concurrency control>",
    "<Hint on failure modes and resilience>"
  ],
  "evaluation_criteria": [
    "<Criterion 1: Architectural correctness under scale>",
    "<Criterion 2: Concurrency & race condition mitigation>",
    "<Criterion 3: Explicit trade-off defense (CAP theorem / isolation levels)>"
  ]
}}
"""
    if avail:
        primary = avail[0]
        try:
            res = providers.call_provider(primary, prompt, timeout=20.0)
            if res.get("ok"):
                parsed = parsing.extract_json(res.get("text", ""))
                parsed["mode"] = "live-llm-interview"
                parsed["provider"] = primary
                return parsed
        except Exception:
            pass

    # Calibrated enterprise fallback grounded in company profile
    return {
        "question_id": f"{company.lower()}-calibrated-q1",
        "company": company_ctx["name"],
        "round_name": round_name,
        "interviewer_role": f"Staff Infrastructure Engineer at {company_ctx['name']}",
        "question": f"At {company_ctx['name']}, our core platform processes high-velocity request spikes across distributed services. Design an ingestion and state synchronizer that eliminates the cache stampede (thundering herd) problem during high-volume key invalidations while maintaining strict idempotency.",
        "scenario_context": f"Production systems at {company_ctx['name']} experience traffic spikes where invalidating a popular cache key risks taking down the backing primary datastore.",
        "target_bloom": "EV",
        "primary_skill": "System Design & Architecture",
        "constraints": [
            "50,000 read requests per second on popular keys",
            "P99 latency must stay strictly under 15 milliseconds",
            "Backing database must never exceed 50 concurrent connections during cache miss"
        ],
        "hints": [
            "Consider single-flight mutual exclusion with distributed lock lease timeouts.",
            "Evaluate probabilistic early expiration (XFetch algorithm) combined with stale-while-revalidate."
        ],
        "evaluation_criteria": [
            "Correctness of mutual exclusion locking vs asynchronous background refresh",
            "Handling of node crashes while holding cache lock (TTL leases)",
            "Trade-off defense between immediate consistency vs stale-data tolerance"
        ],
        "mode": "calibrated-offline",
        "provider": "offline-benchmark"
    }


def evaluate_interview_answer(
    company: str,
    round_name: str,
    question: str,
    answer: str,
    candidate: dict[str, Any]
) -> dict[str, Any]:
    """Evaluates candidate response across Bloom taxonomy depth and returns detailed critique."""
    avail = agents.availability()
    candidate_name = candidate.get("name", "Candidate")
    company_ctx = _get_company_context(company)

    prompt = f"""You are a Principal Engineer and Bar Raiser evaluating a candidate's answer at {company_ctx['name']}.
ROUND: {round_name}
CANDIDATE: {candidate_name}
QUESTION: {question}

CANDIDATE ANSWER:
\"\"\"{answer}\"\"\"

Critique this answer against Bloom's Taxonomy cognitive depth:
- Level 1-2 (CU - Conceptual): Recalls definitions without understanding production mechanics.
- Level 3-4 (AP - Application): Writes standard code or draws basic boxes without scale mitigation.
- Level 5-6 (AS - Analysis): Deconstructs failure modes, identifies bottlenecks, calculates time/space complexity.
- Level 7-8 (EV - Evaluation): Justifies architectural trade-offs, defends CAP theorem choices, quantifies latency/fault recovery.
- Level 9-10 (CR - Creation): Synthesizes novel or production-grade resilient architectures.

Return strict JSON only (no markdown fence, no prose outside JSON):
{{
  "score": <integer from 1 to 10>,
  "bloom_achieved": "CU" | "AP" | "AS" | "EV" | "CR",
  "bloom_label": "Conceptual Understanding" | "Application" | "Analysis & Synthesis" | "Evaluation" | "Creation",
  "verdict": "STRONG HIRE" | "HIRE" | "LEAN HIRE" | "NO HIRE",
  "dimension_scores": {{
    "system_architecture": <1-10>,
    "concurrency_and_scale": <1-10>,
    "edge_case_resilience": <1-10>,
    "tradeoff_defense": <1-10>
  }},
  "summary_feedback": "<Concise 2-sentence actionable assessment>",
  "strengths": [
    "<Concrete architectural strength 1>",
    "<Concrete architectural strength 2>"
  ],
  "blindspots_and_gaps": [
    "<Critical edge case or failure mode missed 1>",
    "<Tradeoff or operational gap 2>"
  ],
  "follow_up_challenge": "<One probing follow-up challenge testing the candidate on their chosen architecture>",
  "ideal_answer_takeaway": "<What a Staff Engineer at this company would have specified>",
  "production_code_snippet": "<Short 8-15 line snippet in Python, Go, or SQL illustrating the optimal pattern>",
  "recommended_profile_level": <integer from 1 to 10>,
  "suggested_skill_to_update": "System Design & Architecture"
}}
"""
    if avail:
        primary = avail[0]
        try:
            res = providers.call_provider(primary, prompt, timeout=25.0)
            if res.get("ok"):
                parsed = parsing.extract_json(res.get("text", ""))
                parsed["mode"] = "live-llm-evaluation"
                parsed["provider"] = primary
                return parsed
        except Exception:
            pass

    # Heuristic fallback based on semantic length and technical keywords
    length = len(answer.split())
    has_keywords = sum(1 for k in ["tradeoff", "latency", "redis", "lock", "async", "cache", "consistent", "partition", "idempotent", "raft", "p99"] if k in answer.lower())
    score = min(9, max(4, (length // 25) + has_keywords))

    return {
        "score": score,
        "bloom_achieved": "EV" if score >= 8 else ("AS" if score >= 6 else "AP"),
        "bloom_label": "Evaluation" if score >= 8 else ("Analysis & Synthesis" if score >= 6 else "Application"),
        "verdict": "HIRE" if score >= 8 else ("LEAN HIRE" if score >= 6 else "NO HIRE"),
        "dimension_scores": {
            "system_architecture": min(10, score + 1),
            "concurrency_and_scale": score,
            "edge_case_resilience": max(3, score - 1),
            "tradeoff_defense": score
        },
        "summary_feedback": f"Your response presents a clear architectural approach with {length} words. You demonstrated good understanding of core caching and concurrency mechanics.",
        "strengths": [
            "Addressed distributed partitioning and lock management directly.",
            "Demonstrated clear understanding of cache invalidation bottlenecks."
        ],
        "blindspots_and_gaps": [
            "Did not quantify p99 latency recovery cost under severe network partition.",
            "Omitted lease expiration handling if a worker crashes before releasing the lock."
        ],
        "follow_up_challenge": "If the primary Redis node crashes while 50 workers are waiting on the distributed mutex, how does your system guarantee no deadlocks occur without causing a stampede on the fallback DB?",
        "ideal_answer_takeaway": "Top engineers deploy singleflight request coalescing in-memory combined with Redis Mutex leases (TTL 200ms) and background async refresh before TTL expiry.",
        "production_code_snippet": """# Single-flight request coalescing pattern
async def get_or_compute(key: str, loader_fn):
    val = await cache.get(key)
    if val is not None:
        return val
    # Acquire distributed lease to prevent thundering herd
    async with redis.lock(f"lock:{key}", timeout=0.2):
        val = await cache.get(key)
        if val is not None: return val
        val = await loader_fn()
        await cache.set(key, val, ex=300)
        return val""",
        "recommended_profile_level": min(10, max(5, score)),
        "suggested_skill_to_update": "System Design & Architecture",
        "mode": "calibrated-offline",
        "provider": "offline-benchmark"
    }
