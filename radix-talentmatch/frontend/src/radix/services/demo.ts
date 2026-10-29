/**
 * In-browser demo engine. Mirrors the FastAPI heuristics (scoring.py,
 * skill_extractor.py, career_radar.py, committee/interview fallbacks) so the
 * app is fully usable without the Python backend. Profiles and assessment
 * history persist in localStorage.
 */
import candidatesSeed from "../data/sample_candidates.json";
import jobsSeed from "../data/sample_job_descriptions.json";
import companySets from "../data/talent_check_company_skillsets.json";
import type {
  Analysis, Assessment, CareerRadarData, CommitteeResult, IntelBundle, IntelStatus,
  InterviewEvaluation, InterviewQuestion, Job, MatchResult, Profile, Skill, TailoredBulletResult,
} from "../types";

const intelFiles = import.meta.glob("../data/intel/*.json", { eager: true, import: "default" }) as Record<string, IntelBundle>;
const INTEL: Record<string, IntelBundle> = {};
for (const b of Object.values(intelFiles)) INTEL[b.company.toLowerCase()] = b;

const PKEY = "radix-demo-profiles";
const AKEY = "radix-demo-assessments";
const hasLS = () => typeof window !== "undefined" && !!window.localStorage;
const read = <T,>(k: string, fb: T): T => {
  if (!hasLS()) return fb;
  try { const v = localStorage.getItem(k); return v ? (JSON.parse(v) as T) : fb; } catch { return fb; }
};
const write = (k: string, v: unknown) => { if (hasLS()) localStorage.setItem(k, JSON.stringify(v)); };
const wait = (ms = 260) => new Promise((r) => setTimeout(r, ms));

const CATEGORY_LABELS: Record<string, string> = {
  COD: "Coding", DSA: "Data Structures & Algorithms", OOD: "Object-Oriented Design", APTI: "Aptitude",
  COMM: "Communication", AI: "Artificial Intelligence", CLOUD: "Cloud", SQL: "SQL", SWE: "Software Engineering",
  SYSD: "System Design", NETW: "Networking", OS: "Operating Systems", OTHER: "Other skills",
};

const TAXONOMY: Record<string, string> = {
  Python: "COD", Java: "COD", JavaScript: "COD", TypeScript: "COD", "C++": "COD", "C#": "COD", Go: "COD", Rust: "COD",
  Kotlin: "COD", Swift: "COD", React: "COD", "Node.js": "COD", Django: "COD", Flask: "COD", FastAPI: "COD",
  "Spring Boot": "COD", HTML: "COD", CSS: "COD", GraphQL: "COD", "REST APIs": "COD",
  "Data Structures and Algorithms": "DSA", "Data Structures": "DSA", Algorithms: "DSA", "Dynamic Programming": "DSA",
  "Object-Oriented Design": "OOD", "Object-Oriented Programming": "OOD", "Design Patterns": "OOD", OOP: "OOD",
  "Problem Solving": "APTI", Statistics: "APTI", Probability: "APTI", Experimentation: "APTI",
  Communication: "COMM", Collaboration: "COMM", Teamwork: "COMM",
  "Machine Learning": "AI", "Deep Learning": "AI", NLP: "AI", "Computer Vision": "AI", PyTorch: "AI",
  TensorFlow: "AI", "scikit-learn": "AI", Pandas: "AI", "Predictive Models": "AI",
  "Cloud Computing": "CLOUD", AWS: "CLOUD", Azure: "CLOUD", GCP: "CLOUD", Docker: "CLOUD", Kubernetes: "CLOUD",
  "CI/CD": "CLOUD", Microservices: "CLOUD",
  SQL: "SQL", PostgreSQL: "SQL", MySQL: "SQL", MongoDB: "SQL", Redis: "SQL", NoSQL: "SQL",
  "Software Engineering": "SWE", Git: "SWE", "Unit Testing": "SWE", Agile: "SWE", "Software Testing": "SWE",
  "System Design": "SYSD", "Distributed Systems": "SYSD", Scalability: "SYSD", Caching: "SYSD", Kafka: "SYSD",
  Networking: "NETW", "TCP/IP": "NETW", HTTP: "NETW", DNS: "NETW",
  "Operating Systems": "OS", Linux: "OS", Unix: "OS", Bash: "OS", Concurrency: "OS", Multithreading: "OS",
  "Data Visualization": "OTHER", Excel: "OTHER", "Power BI": "OTHER",
};
const ALIASES: Record<string, string> = {
  dsa: "Data Structures and Algorithms", datastructuresandalgorithms: "Data Structures and Algorithms",
  oop: "Object-Oriented Programming", objectorientedprogramming: "Object-Oriented Programming",
  js: "JavaScript", javascript: "JavaScript", ml: "Machine Learning", machinelearning: "Machine Learning",
};
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
const canon = (s: string) => norm(ALIASES[norm(s)] || s);

function extractSkills(text: string): Skill[] {
  const found: Skill[] = [];
  const seen = new Set<string>();
  const lower = text.toLowerCase();
  const terms = Object.keys(TAXONOMY).sort((a, b) => b.length - a.length);
  for (const term of terms) {
    const esc = term.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`(^|[^a-z0-9+#])${esc}(?=$|[^a-z0-9+#])`, "i");
    const m = re.exec(lower);
    if (!m) continue;
    const key = canon(term);
    if (seen.has(key)) continue;
    seen.add(key);
    const at = m.index;
    const start = Math.max(0, text.lastIndexOf(".", at) + 1);
    const endDot = text.indexOf(".", at);
    const evidence = text.slice(start, endDot === -1 ? undefined : endDot + 1).trim().slice(0, 220);
    found.push({ skill_name: term, category_code: TAXONOMY[term] ?? "OTHER", evidence, confidence: term.length > 4 ? "high" : "medium" });
  }
  return found;
}

function profiles(): Profile[] {
  return read<Profile[]>(PKEY, candidatesSeed as unknown as Profile[]);
}
function findProfile(id: string) {
  const p = profiles().find((x) => x.id === id);
  if (!p) throw new Error("Candidate not found. Choose another profile.");
  return p;
}
function record(a: Omit<Assessment, "timestamp">) {
  const rows = read<Assessment[]>(AKEY, []);
  rows.unshift({ ...a, timestamp: new Date().toISOString() });
  write(AKEY, rows.slice(0, 50));
}
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `candidate-${Date.now()}`;

function levelsOf(p: Profile) {
  const byName: Record<string, number> = {};
  const byCode: Record<string, number> = {};
  for (const s of p.skills || []) {
    const l = Number(s.level || 0);
    if (l < 1 || l > 10) continue;
    byName[canon(s.skill_name)] = Math.max(byName[canon(s.skill_name)] || 0, l);
    const c = (s.category_code || "OTHER").toUpperCase();
    byCode[c] = Math.max(byCode[c] || 0, l);
  }
  return { byName, byCode };
}

function companyRequirements(company: string) {
  const sets = (companySets as { companies: Record<string, { skill_name: string; category_code: string; required_level: number }[]> }).companies;
  if (sets[company]) return sets[company];
  const bundle = INTEL[company.toLowerCase()];
  if (bundle) {
    return bundle.artifacts.skill_matrix.skills.slice(0, 8).map((s) => ({
      skill_name: s.skill_name, category_code: s.skill_set_code, required_level: s.required_level,
    }));
  }
  throw new Error(`No expectation data for ${company}.`);
}

function parseResume(text: string, file?: string) {
  const email = text.match(/[\w.+-]+@[\w-]+\.[\w.]+/)?.[0] || null;
  const firstLine = text.split("\n").map((l) => l.trim()).find(Boolean) || "";
  const name = firstLine && firstLine.split(" ").length <= 5 && !firstLine.includes("@") ? firstLine : "Not detected";
  const section = (label: RegExp) => {
    const line = text.split("\n").find((l) => label.test(l));
    if (!line) return [];
    return line.replace(/^[^:]*:/, "").split(/;|\u2022/).map((x) => x.trim()).filter(Boolean);
  };
  return {
    name, email, cv_file: file || "pasted-text.txt",
    skills: extractSkills(text).map((s) => ({ ...s, level: 0 })),
    education: section(/^\s*education/i), projects: section(/^\s*projects?/i),
    internships: section(/^\s*internships?/i), hackathons: section(/^\s*hackathons?/i),
    certifications: section(/^\s*certifications?/i), preferred_roles: [],
  };
}

async function fileText(file: File) {
  if (/\.txt$/i.test(file.name) || file.type.startsWith("text/")) return file.text();
  throw new Error("The preview reads TXT files and pasted text. PDF and DOCX parsing needs the RADIX backend.");
}

export const demoApi = {
  profiles: async () => { await wait(120); return profiles(); },
  assessments: async () => { await wait(120); return read<Assessment[]>(AKEY, []); },
  jobs: async () => { await wait(80); return jobsSeed as Job[]; },
  companies: async () => {
    const base = Object.keys((companySets as { companies: Record<string, unknown> }).companies);
    const intel = Object.values(INTEL).filter((b) => b.verified).map((b) => b.company);
    return { companies: Array.from(new Set([...base, ...intel])).sort(), source: "Illustrative demo expectations + bundled research dossiers" };
  },
  getProfile: async (id: string) => findProfile(id),
  createProfile: async (p: Profile) => {
    await wait();
    const all = profiles();
    let id = slug(p.name);
    while (all.some((x) => x.id === id)) id = `${id}-2`;
    const out = { ...p, id };
    write(PKEY, [...all, out]);
    return out;
  },
  saveProfile: async (p: Profile) => {
    await wait();
    write(PKEY, profiles().map((x) => (x.id === p.id ? p : x)));
    return p;
  },
  analyzeText: async (text: string): Promise<Analysis> => {
    await wait(420);
    const first = text.split("\n")[0] || "";
    return {
      title: first.slice(0, 80) || "Job description", company: first.split(" ")[0] || "Unknown",
      source_file: "pasted-text.txt", text, required_skills: extractSkills(text),
      method: "Deterministic taxonomy keyword & phrase extraction · runs in your browser",
    };
  },
  analyzeFile: async (file: File) => {
    const a = await demoApi.analyzeText(await fileText(file));
    return { ...a, source_file: file.name };
  },
  parseText: async (text: string) => { await wait(420); return parseResume(text); },
  parseFile: async (file: File) => parseResume(await fileText(file), file.name),
  talent: async (candidate_id: string, company: string) => {
    await wait(380);
    const p = findProfile(candidate_id);
    const reqs = companyRequirements(company);
    const { byName, byCode } = levelsOf(p);
    let earned = 0;
    const gaps = reqs.map((r) => {
      const code = (r.category_code || "OTHER").toUpperCase();
      const cand = Math.max(byName[canon(r.skill_name)] || 0, byCode[code] || 0);
      earned += Math.min(cand, r.required_level) / r.required_level;
      return {
        skill_name: r.skill_name, category_code: code, required_level: r.required_level, candidate_level: cand,
        gap: Math.max(0, r.required_level - cand), status: cand >= r.required_level ? "Met" : cand ? "Partial" : "Missing",
        explanation: `Profile level ${cand}/10 compared with required level ${r.required_level}/10.`,
      };
    });
    const score = reqs.length ? Math.round((100 * earned) / reqs.length) : 0;
    const bundle = INTEL[company.toLowerCase()];
    record({ type: "readiness", candidate_id, candidate_name: p.name, target: company, score });
    return {
      company, readiness_score: score, skillset_gap: gaps,
      recommendations: gaps.filter((g) => g.status !== "Met").sort((a, b) => b.gap - a.gap)
        .map((g) => `Raise ${g.skill_name} from ${g.candidate_level}/10 to ${g.required_level}/10 with a focused project and add the evidence to your profile.`),
      verification: bundle ? {
        verified: bundle.verified, mode: bundle.mode, researched_at: bundle.researched_at,
        quality_errors: bundle.quality.errors, quality_warnings: bundle.quality.warnings,
        consensus_sources: bundle.artifacts.skill_matrix.consensus_sources, conflicts: bundle.artifacts.skill_matrix.conflicts || [],
      } : undefined,
    };
  },
  match: async (candidate_id: string, job_description_id: string): Promise<MatchResult> => {
    await wait(320);
    const p = findProfile(candidate_id);
    const job = ((jobsSeed as Job[]).find((j) => j.id === job_description_id) || (jobsSeed as Job[])[0]) as Job;
    const req = extractSkills(job.text);
    const { byName } = levelsOf(p);
    const matched: Skill[] = [];
    const missing: Skill[] = [];
    for (const s of req) {
      const key = canon(s.skill_name);
      const ev = (p.skills || []).find((x) => canon(x.skill_name) === key)?.evidence || "";
      const item = { ...s, candidate_level: byName[key] || 0, candidate_evidence: ev };
      (key in byName ? matched : missing).push(item);
    }
    const score = req.length ? Math.round((100 * matched.length) / req.length) : 0;
    const breakdown: MatchResult["category_breakdown"] = {};
    for (const s of req) {
      const b = (breakdown[s.category_code] ||= { label: CATEGORY_LABELS[s.category_code] || s.category_code, required: 0, matched: 0 });
      b.required++;
      if (matched.includes(s as Skill) || matched.some((m) => m.skill_name === s.skill_name)) b.matched++;
    }
    record({ type: "match", candidate_id, candidate_name: p.name, target: `${job.company} · ${job.title}`, score });
    return {
      candidate_id, jd_source_file: job.id, job_title: job.title, match_score: score, matched_skills: matched,
      missing_skills: missing, category_breakdown: breakdown,
      recommendations: missing.slice(0, 5).map((s) => `Build a project or complete focused practice in ${s.skill_name}. Add evidence to your profile.`),
      method: "Score = matched requirements ÷ detected requirements × 100. Rated profile skills only.",
    };
  },
  intelStatus: async (): Promise<IntelStatus> => ({
    providers: [
      { provider: "groq", model: "—", available: false },
      { provider: "openrouter", model: "—", available: false },
    ],
    verified_companies: Object.values(INTEL).map((b) => ({
      company: b.company, mode: b.mode, verified: b.verified, errors: b.quality.errors, warnings: b.quality.warnings, researched_at: b.researched_at,
    })),
    bundled: Object.values(INTEL).map((b) => b.company),
  }),
  intelResearch: async (company: string) => {
    await wait(900);
    const b = INTEL[company.toLowerCase()];
    if (!b) throw new Error(`Live research for "${company}" needs the RADIX backend with an AI provider. Try one of the bundled dossiers.`);
    return b;
  },
  intelCompany: async (company: string) => {
    const b = INTEL[company.toLowerCase()];
    if (!b) throw new Error(`No dossier for ${company} yet.`);
    return b;
  },
  committeeDeliberate: async (candidate_id: string, company: string): Promise<CommitteeResult> => {
    await wait(900);
    const c = findProfile(candidate_id);
    const skills = c.skills || [];
    const avg = skills.reduce((a, s) => a + Number(s.level || 5), 0) / Math.max(1, skills.length);
    const score = Math.round(Math.min(100, Math.max(20, avg * 10 + (c.projects?.length ? 10 : 0))));
    const verdict = score >= 80 ? "OFFER EXTENDED" : score >= 65 ? "OFFER WITH CONDITIONS" : score >= 50 ? "LEANING NO HIRE" : "REJECT";
    return {
      mode: "heuristic-committee", provider: "offline-rules", company, candidate_id,
      consensus_verdict: verdict, consensus_score: score,
      summary_statement: `The committee reviewed ${c.name}'s profile against ${company}'s benchmarks. Average skill rating: ${avg.toFixed(1)}/10.`,
      personas: [
        { name: "Bar Raiser", role: "Guardian of Company Standards", vote: score >= 75 ? "Hire" : "Leaning No Hire", stance: "Baseline competencies are present, but deeper Bloom-level verification is needed before sign-off.", key_concern: "Depth in core Data Structures and System Design trade-offs.", key_endorsement: "Clear academic trajectory and structured skill coverage." },
        { name: "Tech Lead", role: "Engineering Architecture Lead", vote: score >= 65 ? "Hire" : "No Hire", stance: "Practical skills look usable; needs concrete evidence of handling concurrency and distributed edge cases.", key_concern: "No high-traffic production evidence in submitted projects.", key_endorsement: "Solid grasp of core language idioms." },
        { name: "Hiring Manager", role: "Team & Product Lead", vote: score >= 70 ? "Strong Hire" : "Hire", stance: "Strong appetite to learn and high growth trajectory. Would add sprint velocity on junior tasks.", key_concern: "May need 4–6 weeks onboarding on company CI/CD pipelines.", key_endorsement: "Proactive project portfolio and well-maintained profile." },
      ],
      conditions_to_hire: [
        `Demonstrate Evaluation-depth (EV) reasoning in System Design and caching for ${company}.`,
        "Ship and document a deployed service with rate-limiting and query optimisation.",
      ],
      key_differentiator: "Breadth across core engineering domains with demonstrable project motivation.",
    };
  },
  interviewStart: async (_candidate_id: string, company: string, round_name = "System Design"): Promise<InterviewQuestion> => {
    await wait(700);
    return {
      question_id: `${company.toLowerCase()}-calibrated-q1`, company, round_name,
      interviewer_role: `Staff Infrastructure Engineer at ${company}`,
      question: `At ${company}, our core platform processes high-velocity request spikes across distributed services. Design an ingestion and state synchroniser that eliminates the cache stampede (thundering herd) problem during high-volume key invalidations while maintaining strict idempotency.`,
      scenario_context: `Production systems at ${company} see traffic spikes where invalidating a popular cache key risks taking down the primary datastore.`,
      target_bloom: "EV", primary_skill: "System Design & Architecture",
      constraints: ["50,000 reads/sec on popular keys", "P99 latency under 15 ms", "Database never exceeds 50 concurrent connections on a miss"],
      hints: ["Consider single-flight mutual exclusion with lock lease timeouts.", "Evaluate probabilistic early expiration (XFetch) with stale-while-revalidate."],
      evaluation_criteria: ["Mutual exclusion vs background refresh correctness", "Node crashes while holding the lock (TTL leases)", "Consistency vs staleness trade-off defence"],
      mode: "calibrated-offline", provider: "offline-benchmark",
    };
  },
  interviewEvaluate: async (candidate_id: string, _company: string, _round: string, _q: string, answer: string, apply_upgrade = false): Promise<InterviewEvaluation> => {
    await wait(900);
    const a = answer.toLowerCase();
    const kws = ["lock", "lease", "ttl", "stale", "idempot", "jitter", "backoff", "single-flight", "singleflight", "xfetch", "probabilistic", "consisten", "trade", "redis", "queue", "p99", "fallback"];
    const hits = kws.filter((k) => a.includes(k)).length;
    const lenBonus = Math.min(3, Math.floor(answer.trim().split(/\s+/).length / 60));
    const score = Math.max(1, Math.min(10, 2 + hits + lenBonus));
    const bloom: [string, string] = score >= 9 ? ["CR", "Creation"] : score >= 7 ? ["EV", "Evaluation"] : score >= 5 ? ["AS", "Analysis & Synthesis"] : score >= 3 ? ["AP", "Application"] : ["CU", "Conceptual Understanding"];
    const verdict = score >= 8 ? "STRONG HIRE" : score >= 6 ? "HIRE" : score >= 4 ? "LEAN HIRE" : "NO HIRE";
    if (apply_upgrade) {
      const all = profiles();
      write(PKEY, all.map((p) => p.id !== candidate_id ? p : {
        ...p,
        skills: p.skills.some((s) => s.skill_name === "System Design")
          ? p.skills.map((s) => s.skill_name === "System Design" ? { ...s, level: Math.max(Number(s.level || 0), score) } : s)
          : [...p.skills, { skill_name: "System Design", category_code: "SYSD", level: score, evidence: "Verified in Mock Interview Arena", confidence: "medium" }],
      }));
    }
    return {
      score, bloom_achieved: bloom[0], bloom_label: bloom[1], verdict,
      summary_feedback: hits >= 4 ? "You reasoned about failure modes and trade-offs with useful specificity. Quantify recovery behaviour to reach the next level." : "The answer stays at a conceptual level. Name concrete mechanisms (locks, leases, stale-while-revalidate) and defend the trade-offs.",
      strengths: hits ? ["Identified relevant mechanisms for the stampede problem", "Structured the response around the constraints"] : ["Engaged with the problem framing"],
      blindspots_and_gaps: ["What happens when the lock holder crashes mid-refresh?", "How do you bound database connections during a cold start?"],
      follow_up_challenge: "Your lock service itself goes down for 30 seconds. Walk me through the degraded behaviour.",
      ideal_answer_takeaway: "Combine single-flight refresh behind a TTL lease with probabilistic early expiration and serve stale data during refresh, guarded by a connection-pool semaphore.",
      production_code_snippet: "async def get(key):\n    val, ttl = await cache.get_with_ttl(key)\n    if val and not should_early_refresh(ttl):\n        return val\n    if await lock.acquire(key, lease=5):\n        try:\n            val = await db.fetch(key)\n            await cache.set(key, val, ttl=300)\n        finally:\n            await lock.release(key)\n    return val or await cache.get_stale(key)",
      dimension_scores: { system_architecture: Math.min(10, score + 1), concurrency_and_scale: score, edge_case_resilience: Math.max(1, score - 1), tradeoff_defense: score },
      recommended_profile_level: score, suggested_skill_to_update: "System Design", profile_updated: apply_upgrade,
      mode: "heuristic-evaluation", provider: "offline-rules",
    };
  },
  careerRadar: async (candidate_id: string): Promise<CareerRadarData> => {
    await wait(500);
    const c = findProfile(candidate_id);
    const TIERS = {
      super_dream: { label: "Super Dream (Tier 1)", ctc_range: "₹20 LPA – ₹55 LPA", bench: 7.5, companies: ["Google", "Microsoft", "Atlassian", "Uber", "Amazon", "Meta"] },
      dream: { label: "Dream (Tier 2)", ctc_range: "₹10 LPA – ₹20 LPA", bench: 6, companies: ["Zomato", "Swiggy", "Juspay", "Flipkart", "Blinkit", "Razorpay"] },
      standard: { label: "Standard (Tier 3)", ctc_range: "₹4.5 LPA – ₹9 LPA", bench: 4.5, companies: ["Accenture", "Infosys", "TCS", "Wipro", "Cognizant", "Capgemini"] },
    };
    const tiers: CareerRadarData["tiers"] = {};
    for (const [k, m] of Object.entries(TIERS)) {
      const rs = (c.skills || []).map((s) => Math.min(1, Number(s.level || 0) / m.bench));
      const score = rs.length ? Math.round((rs.reduce((a, b) => a + b, 0) / rs.length) * 100) : 30;
      tiers[k] = { label: m.label, ctc_range: m.ctc_range, readiness_score: score, status: score >= 75 ? "Target Qualified" : score >= 55 ? "Competitive" : "Development Needed", representative_companies: m.companies };
    }
    const map = Object.fromEntries((c.skills || []).map((s) => [s.skill_name.toLowerCase(), Number(s.level || 0)]));
    const jumps = ["System Design & Architecture", "Data Structures & Algorithms", "DevOps & Cloud", "Coding"]
      .map((ps) => ({ ps, curr: map[ps.toLowerCase()] ?? 4 })).filter((x) => x.curr < 8).slice(0, 3)
      .map(({ ps, curr }) => ({
        skill: ps, current_level: curr, target_level: Math.min(10, curr + 2), unlocked_tier: "Super Dream",
        estimated_ctc_boost: curr < 6 ? "+₹12 LPA – ₹18 LPA" : "+₹6 LPA – ₹10 LPA",
        reasoning: `Upgrading ${ps} from Level ${curr} to Level ${Math.min(10, curr + 2)} meets the Bloom Evaluation threshold for Tier 1 hiring bars.`,
      }));
    const sd = tiers["super_dream"]?.readiness_score ?? 0;
    const dr = tiers["dream"]?.readiness_score ?? 0;
    return {
      candidate_id: c.id, candidate_name: c.name, tiers, roi_skill_jumps: jumps,
      overall_placement_tier: sd >= 75 ? "Super Dream Ready" : dr >= 65 ? "Dream Tier Ready" : "Standard Tier Qualified",
    };
  },
  tailorBullet: async (skill_name: string, target_company = "Google"): Promise<TailoredBulletResult> => {
    await wait(600);
    return {
      skill_name, target_company,
      ats_bullet: `Engineered a scalable ${skill_name} service handling 15,000+ req/sec, cutting p99 latency by 38% through connection pooling, async caching and Redis cluster sharding.`,
      xyz_breakdown: { accomplished_x: `Engineered a scalable ${skill_name} service`, measured_by_y: "15,000+ req/sec and 38% lower p99 latency", done_by_z: "Connection pooling, async caching and Redis cluster sharding" },
      micro_project_blueprint: {
        project_title: `Production-grade ${skill_name} benchmark suite`, github_repo_slug: `${skill_name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-service`,
        architecture_summary: "FastAPI service in Docker with async workers, Prometheus metrics and distributed caching.",
        deliverables: ["REST & WebSocket endpoints with validation", "k6 load test at 5,000 concurrent users", "Docker Compose + GitHub Actions test workflow"],
      },
      mode: "heuristic-tailoring",
    };
  },
};
