import { useEffect, useState } from 'react';
import { ElevatedCard } from '@cred/neopop-web/lib/components';
import {
  Mic, Brain, Award, CheckCircle2, AlertTriangle, Sparkles, Loader2,
  Terminal, ShieldCheck, ChevronRight, BookOpen, Lightbulb, Zap, Send
} from 'lucide-react';
import { api } from '../services/api';
import type { Profile, InterviewQuestion, InterviewEvaluation } from '../types';

const ROUNDS = [
  'Round 1: Screening & Core CS',
  'Round 2: Technical Interview',
  'Round 3: System Design & Deep Dive',
  'Round 4: Bar Raiser & Behavioral'
];

export function InterviewArena() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [candidateId, setCandidateId] = useState<string>('');
  const [companies, setCompanies] = useState<string[]>([]);
  const [company, setCompany] = useState<string>('Google');
  const [roundName, setRoundName] = useState<string>('Round 2: Technical Interview');

  const [loadingQuestion, setLoadingQuestion] = useState<boolean>(false);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [upgrading, setUpgrading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const [activeQuestion, setActiveQuestion] = useState<InterviewQuestion | null>(null);
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null);
  const [profileUpdated, setProfileUpdated] = useState<boolean>(false);

  useEffect(() => {
    Promise.all([api.profiles(), api.companies()])
      .then(([pList, cList]) => {
        setProfiles(pList);
        if (pList.length) setCandidateId(pList[0].id);
        setCompanies(cList.companies);
        if (cList.companies.length) setCompany(cList.companies[0]);
      })
      .catch((e) => setError(e.message));
  }, []);

  const startSession = async () => {
    if (!candidateId || !company) return;
    setLoadingQuestion(true);
    setError('');
    setActiveQuestion(null);
    setEvaluation(null);
    setUserAnswer('');
    setProfileUpdated(false);

    try {
      const q = await api.interviewStart(candidateId, company, roundName);
      setActiveQuestion(q);
    } catch (e: any) {
      setError(e.message || 'Failed to start interview session');
    } finally {
      setLoadingQuestion(false);
    }
  };

  const submitAnswer = async (applyUpgrade: boolean = false) => {
    if (!activeQuestion || !userAnswer.trim()) return;
    if (applyUpgrade) {
      setUpgrading(true);
    } else {
      setEvaluating(true);
    }
    setError('');

    try {
      const result = await api.interviewEvaluate(
        candidateId,
        company,
        roundName,
        activeQuestion.question,
        userAnswer,
        applyUpgrade
      );
      setEvaluation(result);
      if (applyUpgrade && result.profile_updated) {
        setProfileUpdated(true);
        // Refresh profiles to reflect upgrade
        api.profiles().then(setProfiles).catch(() => {});
      }
    } catch (e: any) {
      setError(e.message || 'Evaluation failed');
    } finally {
      setEvaluating(false);
      setUpgrading(false);
    }
  };

  const fillDemoAnswer = () => {
    if (!activeQuestion) return;
    const sample = `To solve this in production at ${company} scale:
1. Architecture & Partitioning: I would partition the ingress traffic across distributed workers using consistent hashing with virtual nodes on MurmurHash3 to eliminate hotspots.
2. Resilience & Circuit Breaking: Wrap downstream dependencies in resilience4j circuit breakers with fallback queues in Redis/Kafka.
3. Concurrency & Isolation: Use optimistic concurrency control (OCC) with version counters in PostgreSQL, ensuring idempotency keys on every transaction.
4. Trade-offs: Prioritize high availability over absolute consistency (AP under CAP theorem), using asynchronous reconciliation jobs for eventual convergence.`;
    setUserAnswer(sample);
  };

  const getVerdictBadge = (verdict: string) => {
    const v = verdict.toUpperCase();
    if (v.includes('STRONG') || v.includes('OFFER') || v.includes('PASS')) {
      return { label: verdict, color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)' };
    }
    if (v.includes('LEAN') || v.includes('CONDITIONAL')) {
      return { label: verdict, color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)' };
    }
    return { label: verdict, color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)' };
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-signal">
          <Mic className="h-3.5 w-3.5" />
          <span>DIFFERENTIATOR 2 · REAL-TIME AI MOCK INTERVIEW ARENA</span>
        </div>
        <h1 className="mt-1 font-display text-3xl tracking-tight text-foreground sm:text-4xl">
          Adaptive Technical Interview Arena
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          Real company-calibrated technical interviews powered by high-speed reasoning. Practice live scenario challenges,
          get mapped against Bloom's Taxonomy, and upgrade your candidate profile with verified interview proof.
        </p>
      </div>

      {/* Cockpit Card */}
      <ElevatedCard backgroundColor="#141417" edgeColors={{ right: '#2A2A31', bottom: '#05966955' }} fullWidth style={{ width: '100%' }}>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Candidate</label>
              <select
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Target Company</label>
              <select
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {companies.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Interview Round</label>
              <select
                value={roundName}
                onChange={(e) => setRoundName(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {ROUNDS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={startSession}
                disabled={loadingQuestion}
                className="flex w-full items-center justify-center gap-2 rounded bg-signal px-4 py-2 text-sm font-semibold text-black transition hover:bg-signal/90 disabled:opacity-50"
              >
                {loadingQuestion ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loadingQuestion ? 'Generating...' : 'Start Interview'}
              </button>
            </div>
          </div>
        </div>
      </ElevatedCard>

      {error && (
        <div className="flex items-center gap-2 rounded border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Question & Answer Stage */}
      {activeQuestion && (
        <div className="space-y-6">
          {/* Question Card */}
          <ElevatedCard backgroundColor="#16161B" edgeColors={{ right: '#2B2B38', bottom: '#3B82F644' }} fullWidth style={{ width: '100%' }}>
            <div className="p-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/30">
                    <Terminal className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground text-base">{activeQuestion.interviewer_role}</h3>
                    <p className="font-mono text-xs text-muted-foreground">{activeQuestion.company} · {activeQuestion.round_name}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 font-mono text-xs text-indigo-300">
                    Target Bloom: {activeQuestion.target_bloom}
                  </span>
                  <span className="rounded border border-border bg-black/40 px-2.5 py-1 font-mono text-xs text-muted-foreground">
                    Skill: {activeQuestion.primary_skill}
                  </span>
                </div>
              </div>

              {activeQuestion.scenario_context && (
                <div className="mt-4 rounded border border-border/60 bg-black/30 p-4 text-xs leading-relaxed text-muted-foreground font-mono">
                  <strong className="text-foreground">System Context:</strong> {activeQuestion.scenario_context}
                </div>
              )}

              <div className="mt-4">
                <div className="text-xs font-mono uppercase tracking-wider text-signal mb-1.5">Interview Question</div>
                <p className="text-base text-foreground font-medium leading-relaxed bg-black/40 p-4 rounded border border-signal/20">
                  {activeQuestion.question}
                </p>
              </div>

              {activeQuestion.constraints && activeQuestion.constraints.length > 0 && (
                <div className="mt-4 rounded border border-rose-500/20 bg-rose-500/5 p-3.5">
                  <div className="text-[0.68rem] font-mono uppercase tracking-wider text-rose-400 font-semibold mb-2">
                    Production System Constraints & Non-Negotiables:
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {activeQuestion.constraints.map((c, idx) => (
                      <div key={idx} className="rounded bg-black/40 border border-border/60 p-2 text-xs font-mono text-foreground/90 flex items-start gap-1.5">
                        <span className="text-rose-400 font-bold">•</span>
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeQuestion.hints && activeQuestion.hints.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 items-center">
                  <span className="text-xs text-muted-foreground flex items-center gap-1 font-mono">
                    <Lightbulb className="h-3.5 w-3.5 text-amber-400" /> Rubric Hints:
                  </span>
                  {activeQuestion.hints.map((hint, idx) => (
                    <span key={idx} className="rounded bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-xs text-amber-300 font-mono">
                      {hint}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </ElevatedCard>

          {/* User Answer Card */}
          <ElevatedCard backgroundColor="#141417" edgeColors={{ right: '#2A2A31', bottom: '#10B98144' }} fullWidth style={{ width: '100%' }}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-3">
                <label className="font-mono text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <span>Your Architectural & Technical Response</span>
                </label>
                <button
                  type="button"
                  onClick={fillDemoAnswer}
                  className="font-mono text-xs text-signal hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <Sparkles className="h-3 w-3" /> Auto-fill sample answer (Demo)
                </button>
              </div>

              <textarea
                rows={7}
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Explain your approach, architectural trade-offs, concurrency handling, failure scenarios, and concrete algorithms..."
                className="w-full rounded border border-border bg-black/50 p-4 font-mono text-sm text-foreground focus:border-signal focus:outline-none leading-relaxed"
              />

              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs font-mono text-muted-foreground">
                  {userAnswer.length} characters typed
                </span>
                <button
                  onClick={() => submitAnswer(false)}
                  disabled={evaluating || !userAnswer.trim()}
                  className="flex items-center gap-2 rounded bg-signal px-6 py-2.5 text-sm font-semibold text-black transition hover:bg-signal/90 disabled:opacity-50"
                >
                  {evaluating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {evaluating ? 'Evaluating with AI Rubric...' : 'Submit Answer for Critique'}
                </button>
              </div>
            </div>
          </ElevatedCard>
        </div>
      )}

      {/* Evaluation Results */}
      {evaluation && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <ElevatedCard backgroundColor="#15151A" edgeColors={{ right: '#2B2B38', bottom: '#10B98166' }} fullWidth style={{ width: '100%' }}>
            <div className="p-6">
              {/* Verdict Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-5">
                <div className="flex items-center gap-4">
                  <div
                    className="flex h-16 w-16 items-center justify-center rounded-xl border text-2xl font-bold font-mono"
                    style={{
                      borderColor: getVerdictBadge(evaluation.verdict).color,
                      backgroundColor: getVerdictBadge(evaluation.verdict).bg,
                      color: getVerdictBadge(evaluation.verdict).color,
                    }}
                  >
                    {evaluation.score}
                    <span className="text-xs text-muted-foreground font-normal">/10</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded px-2.5 py-0.5 font-mono text-xs font-semibold border"
                        style={{
                          borderColor: getVerdictBadge(evaluation.verdict).color,
                          color: getVerdictBadge(evaluation.verdict).color,
                          backgroundColor: getVerdictBadge(evaluation.verdict).bg,
                        }}
                      >
                        {evaluation.verdict}
                      </span>
                      <span className="font-mono text-xs text-muted-foreground">
                        via {evaluation.provider}
                      </span>
                    </div>
                    <div className="mt-1 font-display text-xl text-foreground">
                      Bloom Level: <span className="text-signal">{evaluation.bloom_achieved} ({evaluation.bloom_label})</span>
                    </div>
                  </div>
                </div>

                {/* Profile Upgrade Action */}
                {evaluation.recommended_profile_level && (
                  <div className="flex items-center gap-3">
                    {profileUpdated ? (
                      <div className="flex items-center gap-2 rounded border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 font-mono text-xs text-emerald-400">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Profile Upgraded to Level {evaluation.recommended_profile_level}!</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => submitAnswer(true)}
                        disabled={upgrading}
                        className="flex items-center gap-2 rounded border border-signal bg-signal/10 px-4 py-2 font-mono text-xs font-semibold text-signal transition hover:bg-signal hover:text-black disabled:opacity-50"
                      >
                        {upgrading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
                        {upgrading ? 'Upgrading Profile...' : `Apply Level ${evaluation.recommended_profile_level} Upgrade to Profile`}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* 4-Dimension Scorecard */}
              {evaluation.dimension_scores && (
                <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(evaluation.dimension_scores).map(([dim, val]) => (
                    <div key={dim} className="rounded border border-border/60 bg-black/40 p-3">
                      <div className="flex justify-between items-center text-[0.68rem] font-mono uppercase text-muted-foreground mb-1">
                        <span>{dim.replace(/_/g, ' ')}</span>
                        <span className="text-signal font-bold">{val}/10</span>
                      </div>
                      <div className="h-1.5 w-full bg-black/60 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-signal transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(0, val * 10))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Summary */}
              <div className="mt-5 text-sm text-foreground leading-relaxed bg-black/30 p-4 rounded border border-border/50">
                <strong className="text-signal font-mono uppercase text-xs block mb-1">Interviewer's Assessment:</strong>
                {evaluation.summary_feedback}
              </div>

              {/* Probing Follow-Up Challenge */}
              {evaluation.follow_up_challenge && (
                <div className="mt-5 rounded border border-indigo-500/40 bg-indigo-500/10 p-4 space-y-2">
                  <div className="flex items-center gap-2 font-mono text-xs text-indigo-300 font-semibold">
                    <Terminal className="h-4 w-4" /> Live Interviewer Follow-Up Probe
                  </div>
                  <p className="text-sm text-foreground/95 font-medium leading-relaxed font-mono">
                    "{evaluation.follow_up_challenge}"
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Tip: Senior engineers distinguish themselves by addressing this follow-up challenge in their revised design.
                  </p>
                </div>
              )}

              {/* Strengths & Blindspots */}
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded border border-emerald-500/30 bg-emerald-500/5 p-4">
                  <div className="flex items-center gap-2 font-mono text-xs text-emerald-400 font-semibold mb-3">
                    <CheckCircle2 className="h-4 w-4" /> Demonstrated Strengths
                  </div>
                  <ul className="space-y-2">
                    {evaluation.strengths.map((s, idx) => (
                      <li key={idx} className="text-xs text-foreground/90 flex items-start gap-2">
                        <span className="text-emerald-400 mt-0.5">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded border border-amber-500/30 bg-amber-500/5 p-4">
                  <div className="flex items-center gap-2 font-mono text-xs text-amber-400 font-semibold mb-3">
                    <AlertTriangle className="h-4 w-4" /> Blindspots & Gaps
                  </div>
                  <ul className="space-y-2">
                    {evaluation.blindspots_and_gaps.map((g, idx) => (
                      <li key={idx} className="text-xs text-foreground/90 flex items-start gap-2">
                        <span className="text-amber-400 mt-0.5">•</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Ideal Answer Takeaway */}
              {evaluation.ideal_answer_takeaway && (
                <div className="mt-6 rounded border border-cyan-500/30 bg-cyan-500/5 p-4">
                  <div className="flex items-center gap-2 font-mono text-xs text-cyan-400 font-semibold mb-2">
                    <BookOpen className="h-4 w-4" /> Production-Grade Takeaway & Model Solution Snippet
                  </div>
                  <p className="text-xs text-foreground/90 leading-relaxed font-mono">
                    {evaluation.ideal_answer_takeaway}
                  </p>
                </div>
              )}

              {/* Production Code Snippet */}
              {evaluation.production_code_snippet && (
                <div className="mt-5 rounded border border-border bg-black/60 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                      <Terminal className="h-3.5 w-3.5 text-signal" /> Production Code Pattern Reference
                    </span>
                  </div>
                  <pre className="overflow-x-auto rounded bg-black/80 p-3 font-mono text-xs text-signal/90 leading-relaxed border border-border/40">
                    {evaluation.production_code_snippet}
                  </pre>
                </div>
              )}
            </div>
          </ElevatedCard>
        </div>
      )}
    </div>
  );
}
