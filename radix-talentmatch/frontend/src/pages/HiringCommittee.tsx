import { useEffect, useState } from 'react';
import { ElevatedCard } from '@cred/neopop-web/lib/components';
import {
  Users, ShieldAlert, Award, CheckCircle2, XCircle, AlertTriangle,
  Sparkles, Loader2, Target, ArrowRight, BookOpen, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { api } from '../services/api';
import type { Profile, CommitteeResult, CommitteePersona } from '../types';

export function HiringCommittee() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [candidateId, setCandidateId] = useState<string>('');
  const [companies, setCompanies] = useState<string[]>([]);
  const [company, setCompany] = useState<string>('Google');
  const [roleTitle, setRoleTitle] = useState<string>('Software Engineer');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [result, setResult] = useState<CommitteeResult | null>(null);

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

  const runCommittee = async () => {
    if (!candidateId || !company) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await api.committeeDeliberate(candidateId, company, roleTitle);
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Hiring committee deliberation failed');
    } finally {
      setLoading(false);
    }
  };

  const getVoteColor = (vote: string) => {
    const v = vote.toLowerCase();
    if (v.includes('strong hire')) return 'border-emerald-500 text-emerald-400 bg-emerald-500/10';
    if (v.includes('hire')) return 'border-cyan-500 text-cyan-400 bg-cyan-500/10';
    if (v.includes('lean')) return 'border-amber-500 text-amber-400 bg-amber-500/10';
    return 'border-rose-500 text-rose-400 bg-rose-500/10';
  };

  const getVerdictBadge = (verdict: string) => {
    const v = verdict.toUpperCase();
    if (v.includes('OFFER') || v.includes('STRONG HIRE')) {
      return { label: verdict, color: '#10B981', icon: CheckCircle2, bg: 'rgba(16, 185, 129, 0.15)' };
    }
    if (v.includes('CONDITIONS') || v.includes('LEAN')) {
      return { label: verdict, color: '#F59E0B', icon: AlertTriangle, bg: 'rgba(245, 158, 11, 0.15)' };
    }
    return { label: verdict, color: '#EF4444', icon: XCircle, bg: 'rgba(239, 68, 68, 0.15)' };
  };

  const selectedCandidate = profiles.find((p) => p.id === candidateId);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-signal">
          <Users className="h-3.5 w-3.5" />
          <span>DIFFERENTIATOR 1 · MULTI-AGENT HIRING COMMITTEE</span>
        </div>
        <h1 className="mt-1 font-display text-3xl tracking-tight text-foreground sm:text-4xl">
          Hiring Committee Deliberation
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          Top tech companies never rely on a single score. Convene a live 3-persona panel (Bar Raiser, Tech Lead, Hiring Manager)
          to debate candidate depth, vote with explicit friction points, and deliver actionable conditions to flip skeptical votes to <span className="font-semibold text-foreground">Hire</span>.
        </p>
      </div>

      {/* Cockpit Card */}
      <ElevatedCard backgroundColor="#141417" edgeColors={{ right: '#2A2A31', bottom: '#05966955' }} fullWidth style={{ width: '100%' }}>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Candidate Profile</label>
              <select
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.skills?.length || 0} skills)
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
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Role Title</label>
              <input
                type="text"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                placeholder="Software Engineer"
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-border/50 pt-4">
            <div className="text-xs text-muted-foreground">
              Candidate: <b className="text-foreground">{selectedCandidate?.name || 'Selected'}</b> · Target: <b className="text-signal">{company}</b>
            </div>
            <button
              onClick={runCommittee}
              disabled={loading || !candidateId}
              className="flex items-center gap-2 rounded bg-signal px-5 py-2 font-mono text-xs uppercase tracking-wider text-black transition-all hover:brightness-110 active:translate-y-px disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {loading ? 'Committee in Deliberation…' : 'Convene Hiring Committee'}
            </button>
          </div>
        </div>
      </ElevatedCard>

      {error && (
        <div className="flex items-center gap-2 rounded border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          <XCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Deliberation Results */}
      {result && (
        <div className="space-y-6">
          {/* Big Consensus Verdict Card */}
          {(() => {
            const badge = getVerdictBadge(result.consensus_verdict);
            const Icon = badge.icon;
            return (
              <div
                className="rounded-lg border p-6 backdrop-blur-md"
                style={{ borderColor: badge.color + '55', background: badge.bg }}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full" style={{ background: badge.color + '33' }}>
                      <Icon className="h-6 w-6" style={{ color: badge.color }} />
                    </div>
                    <div>
                      <div className="font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Consensus Committee Verdict</div>
                      <h2 className="font-display text-2xl font-bold tracking-tight" style={{ color: badge.color }}>
                        {result.consensus_verdict}
                      </h2>
                    </div>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-3xl font-extrabold text-foreground">{result.consensus_score}</span>
                    <span className="font-mono text-xs text-muted-foreground">/ 100 Committee Confidence</span>
                  </div>
                </div>

                <p className="mt-4 text-sm text-foreground/90">{result.summary_statement}</p>

                {result.key_differentiator && (
                  <div className="mt-3 inline-flex items-center gap-2 rounded border border-border bg-black/40 px-3 py-1 font-mono text-xs text-signal">
                    <Award className="h-3.5 w-3.5" />
                    <span>Key Differentiator: {result.key_differentiator}</span>
                  </div>
                )}
              </div>
            );
          })()}

          {/* 3 Personas Grid */}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
            {result.personas?.map((p, i) => (
              <ElevatedCard
                key={i}
                backgroundColor="#18181C"
                edgeColors={{ right: '#2E2E35', bottom: '#3B82F644' }}
                fullWidth
                style={{ width: '100%' }}
              >
                <div className="flex h-full flex-col p-5">
                  <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-3">
                    <div>
                      <b className="font-display text-base text-foreground">{p.name}</b>
                      <p className="font-mono text-[0.62rem] uppercase text-muted-foreground">{p.role}</p>
                    </div>
                    <span className={`rounded border px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-wider font-semibold ${getVoteColor(p.vote)}`}>
                      {p.vote}
                    </span>
                  </div>

                  {/* Stance Quote */}
                  <blockquote className="my-3.5 flex-1 border-l-2 border-signal/60 pl-3 italic text-xs leading-relaxed text-foreground/80">
                    “{p.stance}”
                  </blockquote>

                  {/* Concerns & Endorsement */}
                  <div className="space-y-2 border-t border-border/50 pt-3 text-[0.7rem]">
                    <div className="flex items-start gap-1.5 text-rose-300">
                      <ThumbsDown className="mt-0.5 h-3 w-3 shrink-0 text-rose-400" />
                      <span><b>Reservation:</b> {p.key_concern}</span>
                    </div>
                    <div className="flex items-start gap-1.5 text-emerald-300">
                      <ThumbsUp className="mt-0.5 h-3 w-3 shrink-0 text-emerald-400" />
                      <span><b>Highlight:</b> {p.key_endorsement}</span>
                    </div>
                  </div>
                </div>
              </ElevatedCard>
            ))}
          </div>

          {/* Conditions to Flip Vote Card */}
          {result.conditions_to_hire?.length > 0 && (
            <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-6">
              <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-amber-400">
                <Target className="h-4 w-4" />
                <span>Conditions to Flip Skeptical Votes to "Hire"</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Actionable proofs required by the Bar Raiser and Tech Lead to unblock an official offer letter:
              </p>
              <ul className="mt-3 space-y-2">
                {result.conditions_to_hire.map((cond, ci) => (
                  <li key={ci} className="flex items-start gap-2.5 text-xs text-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-amber-500/20 font-mono text-[0.65rem] text-amber-300">
                      {ci + 1}
                    </span>
                    <span className="leading-5">{cond}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
export default HiringCommittee;
