// @ts-nocheck, legacy RADIX screen ported as-is; typed against the original lax tsconfig.
import { useEffect, useState } from 'react';
import { ElevatedCard } from '@cred/neopop-web/lib/components';
import {Users,ShieldAlert,Award,CheckCircle2,XCircle,AlertTriangle,ArrowRight,Loader2,Target,BookOpen,ThumbsUp,ThumbsDown} from 'lucide-react';
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
    if (v.includes('strong hire')) return 'border-tier-standard text-tier-standard bg-tier-standard/10';
    if (v.includes('hire')) return 'border-tier-dream text-tier-dream bg-tier-dream/10';
    if (v.includes('lean')) return 'border-signal text-signal bg-signal/10';
    return 'border-crit text-crit bg-crit/10';
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
      <header className="page-head"><div><div className="eyebrow page-eyebrow">Lab · Committee</div><h1>The hiring committee</h1><p>A bar raiser, a tech lead and a hiring manager review the profile, vote, and say exactly what would change their mind.</p></div></header>

      {/* Cockpit Card */}
      <ElevatedCard backgroundColor="#141417" edgeColors={{ right: '#2A2A31', bottom: '#05966955' }} fullWidth style={{ width: '100%' }}>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Candidate</label>
              <select
                value={candidateId}
                onChange={(e) => setCandidateId(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.skills?.length || 0} skills)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Company</label>
              <select
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {companies.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Role</label>
              <input
                type="text"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                placeholder="Software Engineer"
                className="mt-1.5 w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
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
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              {loading ? 'Committee in Deliberation…' : 'Convene the committee'}
            </button>
          </div>
        </div>
      </ElevatedCard>

      {error && (
        <div className="flex items-center gap-2 rounded border border-crit/30 bg-crit/10 p-4 text-sm text-crit">
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
                      <div className="font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Verdict</div>
                      <h2 className="font-display text-2xl font-bold tracking-tight" style={{ color: badge.color }}>
                        {result.consensus_verdict}
                      </h2>
                    </div>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-3xl font-extrabold text-foreground">{result.consensus_score}</span>
                    <span className="font-mono text-xs text-muted-foreground">/ 100 confidence</span>
                  </div>
                </div>

                <p className="mt-4 text-sm text-foreground/90">{result.summary_statement}</p>

                {result.key_differentiator && (
                  <div className="mt-3 inline-flex items-center gap-2 rounded border border-border bg-background px-3 py-1 font-mono text-xs text-signal">
                    <Award className="h-3.5 w-3.5" />
                    <span>What stands out: {result.key_differentiator}</span>
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
                    <div className="flex items-start gap-1.5 text-crit">
                      <ThumbsDown className="mt-0.5 h-3 w-3 shrink-0 text-crit" />
                      <span><b>Reservation:</b> {p.key_concern}</span>
                    </div>
                    <div className="flex items-start gap-1.5 text-tier-standard">
                      <ThumbsUp className="mt-0.5 h-3 w-3 shrink-0 text-tier-standard" />
                      <span><b>Highlight:</b> {p.key_endorsement}</span>
                    </div>
                  </div>
                </div>
              </ElevatedCard>
            ))}
          </div>

          {/* Conditions to Flip Vote Card */}
          {result.conditions_to_hire?.length > 0 && (
            <div className="rounded-lg border border-signal/40 bg-signal/5 p-6">
              <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-signal">
                <Target className="h-4 w-4" />
                <span>What would turn this into a yes</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Actionable proofs required by the Bar Raiser and Tech Lead to unblock an official offer letter:
              </p>
              <ul className="mt-3 space-y-2">
                {result.conditions_to_hire.map((cond, ci) => (
                  <li key={ci} className="flex items-start gap-2.5 text-xs text-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-signal/20 font-mono text-[0.65rem] text-signal">
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
