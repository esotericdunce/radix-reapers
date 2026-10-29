"""Career Radar, Multi-Company Tier Matching, and ATS Resume Tailoring Agent."""
from __future__ import annotations

import json
from typing import Any
from app.intelligence import agents, parsing, providers, store, supabase_source
from app.utils.scoring import readiness


TIER_DEFINITIONS = {
    "super_dream": {
        "label": "Super Dream (Tier 1)",
        "ctc_range": "₹20 LPA – ₹55 LPA",
        "benchmark_level": 7.5,
        "companies": ["Google", "Microsoft", "Atlassian", "Uber", "Amazon", "Meta"]
    },
    "dream": {
        "label": "Dream (Tier 2)",
        "ctc_range": "₹10 LPA – ₹20 LPA",
        "benchmark_level": 6.0,
        "companies": ["Zomato", "Swiggy", "Juspay", "Flipkart", "Blinkit", "Razorpay"]
    },
    "standard": {
        "label": "Standard (Tier 3)",
        "ctc_range": "₹4.5 LPA – ₹9 LPA",
        "benchmark_level": 4.5,
        "companies": ["Accenture", "Infosys", "TCS", "Wipro", "Cognizant", "Capgemini"]
    }
}


def compute_career_radar(candidate: dict[str, Any]) -> dict[str, Any]:
    """Evaluates candidate across all placement tiers and recommends highest-ROI skill jumps."""
    skills = candidate.get("skills", [])
    skill_map = {s.get("skill_name", "").lower(): int(s.get("level", 0)) for s in skills}

    tier_results = {}
    for tier_key, meta in TIER_DEFINITIONS.items():
        bench = meta["benchmark_level"]
        # Calculate readiness for this tier
        relevant_scores = []
        for s in skills:
            lvl = int(s.get("level", 0))
            ratio = min(1.0, lvl / bench)
            relevant_scores.append(ratio)
        tier_score = round((sum(relevant_scores) / max(1, len(relevant_scores))) * 100) if relevant_scores else 30
        tier_results[tier_key] = {
            "label": meta["label"],
            "ctc_range": meta["ctc_range"],
            "readiness_score": tier_score,
            "status": "Target Qualified" if tier_score >= 75 else ("Competitive" if tier_score >= 55 else "Development Needed"),
            "representative_companies": meta["companies"],
        }

    # Find highest ROI skill jump (e.g. System Design, DSA, Cloud)
    priority_skills = ["System Design & Architecture", "Data Structures & Algorithms", "DevOps & Cloud", "Coding"]
    gaps = []
    for ps in priority_skills:
        curr = skill_map.get(ps.lower(), 4)
        if curr < 8:
            gaps.append({
                "skill": ps,
                "current_level": curr,
                "target_level": min(10, curr + 2),
                "unlocked_tier": "Super Dream",
                "estimated_ctc_boost": "+₹12 LPA – ₹18 LPA" if curr < 6 else "+₹6 LPA – ₹10 LPA",
                "reasoning": f"Upgrading {ps} from Level {curr} to Level {min(10, curr+2)} satisfies the Bloom Evaluation threshold for Tier 1 Super Dream hiring bars."
            })

    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("name"),
        "tiers": tier_results,
        "roi_skill_jumps": gaps[:3],
        "overall_placement_tier": (
            "Super Dream Ready" if tier_results["super_dream"]["readiness_score"] >= 75 else
            ("Dream Tier Ready" if tier_results["dream"]["readiness_score"] >= 65 else "Standard Tier Qualified")
        )
    }


def tailor_resume_bullet(skill_name: str, target_company: str, target_bloom: str = "EV") -> dict[str, Any]:
    """Generates an ATS-compliant, Google XYZ formula resume bullet point + micro-project blueprint."""
    avail = agents.availability()
    prompt = f"""You are a Silicon Valley Technical Resume Coach.
Skill to showcase: {skill_name}
Target Company: {target_company}
Target Bloom Level: {target_bloom} (Evaluation / Architecture depth)

Generate ONE high-impact, ATS-optimized resume bullet point using Google's X-Y-Z formula:
\"Accomplished [X] as measured by [Y], by doing [Z]\"

Also outline a realistic 48-hour weekend micro-project blueprint the candidate can build to legitimately prove this on GitHub.

Output STRICT JSON only:
{{
  "skill_name": "{skill_name}",
  "target_company": "{target_company}",
  "ats_bullet": "<The bullet point with strong action verbs and quantified impact>",
  "xyz_breakdown": {{
    "accomplished_x": "<What was built/improved>",
    "measured_by_y": "<Quantifiable metric: % latency reduction, throughput, reliability>",
    "done_by_z": "<Technologies and architectural decisions used>"
  }},
  "micro_project_blueprint": {{
    "project_title": "<Concise project name>",
    "github_repo_slug": "<e.g. distributed-cache-sentinel>",
    "architecture_summary": "<2-sentence tech stack & design>",
    "deliverables": [
      "<Core feature 1>",
      "<Load test / benchmark deliverable 2>",
      "<CI/CD or Docker containerization 3>"
    ]
  }}
}}
"""
    if avail:
        primary = avail[0]
        try:
            res = providers.call_provider(primary, prompt, timeout=20.0)
            if res.get("ok"):
                parsed = parsing.extract_json(res.get("text", ""))
                parsed["mode"] = "live-llm-tailoring"
                return parsed
        except Exception:
            pass

    return {
        "skill_name": skill_name,
        "target_company": target_company,
        "ats_bullet": f"Engineered scalable {skill_name} microservice handling 15,000+ req/sec, reducing p99 latency by 38% through optimized connection pooling, asynchronous caching, and Redis cluster sharding.",
        "xyz_breakdown": {
            "accomplished_x": f"Engineered scalable {skill_name} microservice",
            "measured_by_y": "15,000+ req/sec throughput and 38% p99 latency reduction",
            "done_by_z": "Optimized connection pooling, asynchronous caching, and Redis cluster sharding"
        },
        "micro_project_blueprint": {
            "project_title": f"Production-Grade {skill_name} Benchmark Suite",
            "github_repo_slug": f"{skill_name.lower().replace(' ', '-')}-service",
            "architecture_summary": f"FastAPI service containerized with Docker, implementing asynchronous workers, Prometheus metrics, and distributed caching.",
            "deliverables": [
                "Implement end-to-end REST & WebSocket endpoints with pydantic validation.",
                "Execute Locust / k6 load test simulating 5,000 concurrent virtual users.",
                "Package with Docker Compose and GitHub Actions automated test workflow."
            ]
        },
        "mode": "heuristic-tailoring"
    }
