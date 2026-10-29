import { useEffect, useState } from 'react';
import { ElevatedCard } from '@cred/neopop-web/lib/components';
import {
  Compass, TrendingUp, Award, CheckCircle2, AlertCircle, Sparkles,
  Loader2, ArrowUpRight, Copy, Check, Terminal, FolderGit2, Zap, Building2
} from 'lucide-react';
import { api } from '../services/api';
import type { Profile, CareerRadarData, RoiJump, TailoredBulletResult } from '../types';

export function CareerRadar() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [candidateId, setCandidateId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [radar, setRadar] = useState<CareerRadarData | null>(null);

  // Resume Tailor Modal / Drawer state
  const [tailorModalOpen, setTailorModalOpen] = useState<boolean>(false);
  const [selectedJump, setSelectedJump] = useState<RoiJump | null>(null);
  const [targetCompany, setTargetCompany] = useState<string>('Google');
  const [tailorLoading, setTailorLoading] = useState<boolean>(false);
  const [tailorResult, setTailorResult] = useState<TailoredBulletResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    api.profiles()
      .then((pList) => {
        setProfiles(pList);
        if (pList.length) {
          setCandidateId(pList[0].id);
          fetchRadar(pList[0].id);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  const fetchRadar = async (cid: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await api.careerRadar(cid);
      setRadar(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load career radar');
    } finally {
      setLoading(false);
    }
  };

  const handleCandidateChange = (cid: string) => {
    setCandidateId(cid);
    fetchRadar(cid);
  };

  const openTailorBlueprint = async (jump: RoiJump) => {
    setSelectedJump(jump);
    setTailorModalOpen(true);
    setTailorResult(null);
    setTailorLoading(true);
    try {
      const res = await api.tailorBullet(jump.skill, targetCompany, 'EV');
      setTailorResult(res);
    } catch (e: any) {
      setError(e.message || 'Failed to generate tailored bullet');
    } finally {
      setTailorLoading(false);
    }
  };

  const copyBullet = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTierColor = (status: string) => {
    if (status === 'QUALIFIED') return { border: '#10B981', text: 'text-emerald-400', bg: 'bg-emerald-500/10' };
    if (status === 'NEAR_TARGET') return { border: '#3B82F6', text: 'text-blue-400', bg: 'bg-blue-500/10' };
    return { border: '#F59E0B', text: 'text-amber-400', bg: 'bg-amber-500/10' };
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-signal">
          <Compass className="h-3.5 w-3.5" />
          <span>DIFFERENTIATOR 3 · STRATEGIC CAREER RADAR & CTC ACCELERATOR</span>
        </div>
        <h1 className="mt-1 font-display text-3xl tracking-tight text-foreground sm:text-4xl">
          Placement Tier Radar & ROI Jumps
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          Go beyond single-company assessments. Benchmark candidate readiness across Super Dream, Dream, and Standard tiers,
          uncover the single highest-ROI Bloom skill leaps that boost placement packages by ₹12–18+ LPA, and generate ready-to-deploy ATS project blueprints.
        </p>
      </div>

      {/* Candidate Cockpit */}
      <ElevatedCard backgroundColor="#141417" edgeColors={{ right: '#2A2A31', bottom: '#05966955' }} fullWidth style={{ width: '100%' }}>
        <div className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="w-full sm:w-80">
              <label className="block font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">Candidate Profile</label>
              <select
                value={candidateId}
                onChange={(e) => handleCandidateChange(e.target.value)}
                className="mt-1.5 w-full rounded border border-border bg-black/40 px-3 py-2 text-sm text-foreground focus:border-signal focus:outline-none"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {radar && (
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs uppercase text-muted-foreground">Placement Tier:</span>
                <span className="rounded border border-signal/40 bg-signal/10 px-3 py-1 font-mono text-xs font-semibold text-signal">
                  {radar.overall_placement_tier}
                </span>
              </div>
            )}
          </div>
        </div>
      </ElevatedCard>

      {error && (
        <div className="flex items-center gap-2 rounded border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-signal" />
        </div>
      )}

      {radar && !loading && (
        <div className="space-y-8">
          {/* Tier Readiness Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(radar.tiers).map(([tierKey, info]) => {
              const theme = getTierColor(info.status);
              return (
                <ElevatedCard
                  key={tierKey}
                  backgroundColor="#15151A"
                  edgeColors={{ right: '#272733', bottom: `${theme.border}44` }}
                  fullWidth
                  style={{ width: '100%' }}
                >
                  <div className="p-5 flex flex-col justify-between h-full">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[0.68rem] uppercase tracking-wider text-muted-foreground">
                          {info.label}
                        </span>
                        <span className={`rounded px-2 py-0.5 font-mono text-[0.65rem] font-semibold border ${theme.text} ${theme.bg}`} style={{ borderColor: theme.border }}>
                          {info.status}
                        </span>
                      </div>

                      <div className="mt-2 font-display text-2xl text-foreground font-semibold">
                        {info.ctc_range}
                      </div>

                      {/* Score Bar */}
                      <div className="mt-4">
                        <div className="flex justify-between text-xs font-mono text-muted-foreground mb-1">
                          <span>Readiness Index</span>
                          <span className="text-foreground font-semibold">{info.readiness_score}%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-black/50 overflow-hidden border border-border/40">
                          <div
                            className="h-full transition-all duration-700"
                            style={{
                              width: `${Math.min(100, Math.max(0, info.readiness_score))}%`,
                              backgroundColor: theme.border,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-border/40">
                      <div className="text-[0.65rem] font-mono uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1">
                        <Building2 className="h-3 w-3" /> Representative Recruiters:
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {info.representative_companies.map((co) => (
                          <span key={co} className="rounded bg-black/40 border border-border px-2 py-0.5 font-mono text-[0.68rem] text-foreground/80">
                            {co}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </ElevatedCard>
              );
            })}
          </div>

          {/* Highest ROI Skill Jumps */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-display text-xl text-foreground">Highest-ROI Skill Upgrades</h2>
                <p className="text-xs text-muted-foreground">
                  The targeted micro-actions that flip candidates into higher compensation bands.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {radar.roi_skill_jumps.map((jump, idx) => (
                <ElevatedCard
                  key={idx}
                  backgroundColor="#141417"
                  edgeColors={{ right: '#2B2B38', bottom: '#10B98133' }}
                  fullWidth
                  style={{ width: '100%' }}
                >
                  <div className="p-5 flex flex-wrap items-center justify-between gap-4">
                    <div className="space-y-1 max-w-xl">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-foreground text-base">{jump.skill}</span>
                        <span className="font-mono text-xs rounded bg-signal/10 border border-signal/30 text-signal px-2 py-0.5">
                          Level {jump.current_level} → Level {jump.target_level}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {jump.reasoning}
                      </p>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="font-mono text-[0.65rem] uppercase text-muted-foreground">Estimated CTC Lift</div>
                        <div className="font-mono text-base font-bold text-emerald-400">{jump.estimated_ctc_boost}</div>
                        <div className="font-mono text-[0.65rem] text-muted-foreground">{jump.unlocked_tier}</div>
                      </div>

                      <button
                        onClick={() => openTailorBlueprint(jump)}
                        className="flex items-center gap-1.5 rounded border border-signal bg-signal/10 px-4 py-2 font-mono text-xs font-semibold text-signal transition hover:bg-signal hover:text-black"
                      >
                        <Zap className="h-3.5 w-3.5" />
                        <span>ATS Bullet & Project</span>
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </ElevatedCard>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ATS Blueprint Modal */}
      {tailorModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-3xl rounded-xl border border-border bg-[#131317] p-6 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border/60 pb-4">
              <div>
                <div className="font-mono text-xs uppercase tracking-wider text-signal flex items-center gap-2">
                  <Terminal className="h-4 w-4" /> Google X-Y-Z Resume Bullet & 48-Hour Micro-Project
                </div>
                <h3 className="font-display text-xl text-foreground mt-1">
                  {selectedJump?.skill} Blueprint
                </h3>
              </div>
              <button
                onClick={() => setTailorModalOpen(false)}
                className="rounded p-1 text-muted-foreground hover:bg-white/10 hover:text-foreground font-mono text-sm"
              >
                ✕ Close
              </button>
            </div>

            {tailorLoading && (
              <div className="flex flex-col items-center justify-center p-12 space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-signal" />
                <span className="font-mono text-xs text-muted-foreground">
                  Synthesizing ATS-optimized STAR bullet and architectural micro-project...
                </span>
              </div>
            )}

            {tailorResult && !tailorLoading && (
              <div className="space-y-6">
                {/* ATS Bullet Card */}
                <div className="rounded-lg border border-signal/30 bg-signal/5 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs uppercase tracking-wider text-signal font-semibold">
                      ATS Verified Resume Bullet (X-Y-Z Formula)
                    </span>
                    <button
                      onClick={() => copyBullet(tailorResult.ats_bullet)}
                      className="flex items-center gap-1.5 rounded border border-signal/40 bg-black/40 px-3 py-1 font-mono text-xs text-signal hover:bg-signal hover:text-black transition cursor-pointer"
                    >
                      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                      <span>{copied ? 'Copied!' : 'Copy Bullet'}</span>
                    </button>
                  </div>

                  <p className="font-mono text-sm text-foreground bg-black/60 p-3.5 rounded border border-border/80 leading-relaxed">
                    • {tailorResult.ats_bullet}
                  </p>

                  {/* XYZ breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-2 text-xs font-mono">
                    <div className="rounded bg-black/40 p-2 border border-border/50">
                      <span className="text-signal font-bold block">[X] Accomplished:</span>
                      <span className="text-muted-foreground">{tailorResult.xyz_breakdown.accomplished_x}</span>
                    </div>
                    <div className="rounded bg-black/40 p-2 border border-border/50">
                      <span className="text-emerald-400 font-bold block">[Y] Measured by:</span>
                      <span className="text-muted-foreground">{tailorResult.xyz_breakdown.measured_by_y}</span>
                    </div>
                    <div className="rounded bg-black/40 p-2 border border-border/50">
                      <span className="text-cyan-400 font-bold block">[Z] Done by:</span>
                      <span className="text-muted-foreground">{tailorResult.xyz_breakdown.done_by_z}</span>
                    </div>
                  </div>
                </div>

                {/* Weekend Project Blueprint */}
                <div className="rounded-lg border border-border bg-black/40 p-4 space-y-3">
                  <div className="flex items-center gap-2 font-mono text-xs uppercase text-muted-foreground">
                    <FolderGit2 className="h-4 w-4 text-cyan-400" />
                    <span>48-Hour Micro-Project to Prove Bloom Depth</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-foreground text-base">
                      {tailorResult.micro_project_blueprint.project_title}
                    </h4>
                    <span className="font-mono text-xs text-muted-foreground bg-black/60 px-2 py-1 rounded border border-border">
                      repo: {tailorResult.micro_project_blueprint.github_repo_slug}
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {tailorResult.micro_project_blueprint.architecture_summary}
                  </p>

                  <div className="pt-2">
                    <span className="text-[0.68rem] font-mono uppercase tracking-wider text-signal block mb-2">
                      Key Engineering Deliverables:
                    </span>
                    <ul className="space-y-1.5">
                      {tailorResult.micro_project_blueprint.deliverables.map((d, i) => (
                        <li key={i} className="text-xs text-foreground/90 flex items-start gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-signal shrink-0 mt-0.5" />
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
