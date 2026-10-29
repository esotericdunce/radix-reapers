"""Multi-Agent Hiring Committee Deliberation Simulator.

Simulates the rigorous, multi-persona consensus process used at top tech companies
(Google, Amazon, Microsoft, Atlassian) before extending an offer.
Features 3 distinct personas:
1. The Bar Raiser: Checks core computer science rigor, long-term trajectory, Bloom depth.
2. The Tech Lead: Scrutinizes scalable architecture, concurrency, clean code, edge cases.
3. The Hiring Manager: Focuses on immediate business delivery, velocity, teamwork.
"""
from __future__ import annotations

import json
from typing import Any
from app.intelligence import agents, parsing, providers
from app.utils.scoring import readiness


def deliberate_candidate(
    candidate: dict[str, Any],
    company: str,
    job_title: str = "Software Engineer",
    job_description: str | None = None
) -> dict[str, Any]:
    avail = agents.availability()
    candidate_name = candidate.get("name", "Candidate")
    skills_summary = ", ".join(
        f"{s.get('skill_name')} (Level {s.get('level', 5)}/10)"
        for s in candidate.get("skills", [])[:12]
    )
    projects_summary = "; ".join(candidate.get("projects", [])[:4]) or "No major projects listed"
    internships_summary = "; ".join(candidate.get("internships", [])[:3]) or "No prior internship recorded"

    system_prompt = f"""You are the Hiring Committee at {company} evaluating candidate {candidate_name} for the role of {job_title}.

CANDIDATE DOSSIER:
- Education: {', '.join(candidate.get('education', [])) or 'Not specified'}
- Assessed Skills: {skills_summary}
- Projects: {projects_summary}
- Internships & Experience: {internships_summary}
{f'- Role Context: {job_description[:300]}' if job_description else ''}

You must convene three distinct Hiring Committee personas to debate:
1. "Bar Raiser": Objective guardian of {company}'s hiring bar. Ruthless on problem-solving rigor and Bloom taxonomy depth.
2. "Tech Lead": Architecture and implementation lead. Focuses on concurrency, edge cases, system scalability, and code cleanliness.
3. "Hiring Manager": Product team manager. Focuses on velocity, practical framework delivery, and proactive communication.

OUTPUT STRICT JSON ONLY:
{{
  "consensus_verdict": "STRONG HIRE" | "OFFER EXTENDED" | "OFFER WITH CONDITIONS" | "LEANING NO HIRE" | "REJECT",
  "consensus_score": <integer 0-100>,
  "summary_statement": "<2-sentence committee summary>",
  "personas": [
    {{
      "name": "Bar Raiser",
      "role": "Guardian of Company Standards",
      "vote": "Strong Hire" | "Hire" | "Leaning No Hire" | "No Hire",
      "stance": "<Direct, candid quote of their argument>",
      "key_concern": "<Single biggest reservation>",
      "key_endorsement": "<Strongest positive observation>"
    }},
    {{
      "name": "Tech Lead",
      "role": "Engineering Architecture Lead",
      "vote": "Strong Hire" | "Hire" | "Leaning No Hire" | "No Hire",
      "stance": "<Direct, candid quote of their argument>",
      "key_concern": "<Single biggest reservation>",
      "key_endorsement": "<Strongest positive observation>"
    }},
    {{
      "name": "Hiring Manager",
      "role": "Team & Product Lead",
      "vote": "Strong Hire" | "Hire" | "Leaning No Hire" | "No Hire",
      "stance": "<Direct, candid quote of their argument>",
      "key_concern": "<Single biggest reservation>",
      "key_endorsement": "<Strongest positive observation>"
    }}
  ],
  "conditions_to_hire": [
    "<Concrete, verifiable technical requirement needed to convert skeptical votes into a definitive Hire>",
    "<Second specific milestone>"
  ],
  "key_differentiator": "<What makes this candidate stand out or fall short>"
}}
"""
    if avail:
        # Use primary available provider (Groq or OpenRouter)
        primary = avail[0]
        try:
            res = providers.call_provider(primary, system_prompt, timeout=25.0)
            if res.get("ok"):
                parsed = parsing.extract_json(res.get("text", ""))
                parsed["mode"] = "live-llm-deliberation"
                parsed["provider"] = primary
                parsed["company"] = company
                parsed["candidate_id"] = candidate.get("id")
                return parsed
        except Exception:
            pass

    # Deterministic offline fallback if LLM is unavailable
    skills = candidate.get("skills", [])
    avg_level = sum(int(s.get("level", 5)) for s in skills) / max(1, len(skills))
    score = int(min(100, max(20, avg_level * 10 + (10 if candidate.get("projects") else 0))))
    verdict = (
        "OFFER EXTENDED" if score >= 80 else
        ("OFFER WITH CONDITIONS" if score >= 65 else
         ("LEANING NO HIRE" if score >= 50 else "REJECT"))
    )

    return {
        "mode": "heuristic-committee",
        "provider": "offline-rules",
        "company": company,
        "candidate_id": candidate.get("id"),
        "consensus_verdict": verdict,
        "consensus_score": score,
        "summary_statement": f"The committee reviewed {candidate_name}'s profile against {company}'s benchmarks. Average skill rating: {avg_level:.1f}/10.",
        "personas": [
            {
                "name": "Bar Raiser",
                "role": "Guardian of Company Standards",
                "vote": "Hire" if score >= 75 else "Leaning No Hire",
                "stance": f"Candidate demonstrates baseline competencies, but we need deeper Bloom-level verification before signing off.",
                "key_concern": "Depth in core Data Structures and System Design tradeoffs.",
                "key_endorsement": "Clear academic trajectory and structured skill coverage."
            },
            {
                "name": "Tech Lead",
                "role": "Engineering Architecture Lead",
                "vote": "Hire" if score >= 65 else "No Hire",
                "stance": f"Practical skills look usable, but need concrete evidence of handling concurrency and distributed edge cases.",
                "key_concern": "Lack of high-traffic production evidence in submitted projects.",
                "key_endorsement": "Solid foundational understanding of core language idioms."
            },
            {
                "name": "Hiring Manager",
                "role": "Team & Product Lead",
                "vote": "Strong Hire" if score >= 70 else "Hire",
                "stance": f"Strong appetite to learn and high growth trajectory. Would add immediate sprint velocity to junior tasks.",
                "key_concern": "May require 4-6 weeks of onboarding on company-specific CI/CD pipelines.",
                "key_endorsement": "Proactive project portfolio and well-maintained profile."
            }
        ],
        "conditions_to_hire": [
            f"Demonstrate Bloom Evaluation depth (EV) in System Design and caching architectures for {company}.",
            "Build and document a deployed service handling rate-limiting and database query optimization."
        ],
        "key_differentiator": "Breadth of core engineering domains with demonstrable project motivation."
    }
