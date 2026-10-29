// @ts-nocheck, legacy RADIX screen ported as-is; typed against the original lax tsconfig.
import { useEffect, useMemo, useState } from 'react';
import {ArrowUpRight,BarChart3,LayoutDashboard,Network,Activity,ScanSearch,UserRound,Radar,Search,Users,Mic,Compass} from 'lucide-react';
import { useNavigate } from '../router';
import { api } from '../services/api';
import type { IntelStatus } from '../types';

const MODULES = [
  ['/', 'Overview', LayoutDashboard],
  ['/jd-analytics', 'JD Analytics', BarChart3],
  ['/resume-parser', 'Resume Parser', ScanSearch],
  ['/profile', 'Profile Builder', UserRound],
  ['/talent-check', 'Talent Check', Activity],
  ['/skill-matching', 'Skill Matching', Network],
  ['/company-intel', 'Company Intelligence Lab', Radar],
  ['/hiring-committee', 'Hiring Committee Deliberation', Users],
  ['/interview-arena', 'Adaptive Mock Interview Arena', Mic],
  ['/career-radar', 'Career Radar & Placement Tiers', Compass],
] as const;

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [bundle, setBundle] = useState<IntelStatus | null>(null);
  useEffect(() => {
    if (open && !bundle) api.intelStatus().then(setBundle).catch(() => setBundle(null));
  }, [open, bundle]);
  useEffect(() => {
    if (open) setQuery('');
  }, [open]);
  const companies = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (bundle?.verified_companies || []).filter((c) => !q || c.company.toLowerCase().includes(q)).slice(0, 6);
    if (q && !list.length && !collectionMatches(query)) return [{ company: query, mode: 'llm-research' } as any];
    return list;
  }, [bundle, query]);
  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    return MODULES.filter(([, label]) => !q || label.toLowerCase().includes(q));
  }, [query]);
  if (!open) return null;
  const go = (to: string) => {
    onClose();
    navigate(to);
  };
  return (
    <div
      className="cmdk-backdrop fixed inset-0 z-[100] flex items-start justify-center bg-background px-4 pt-[12vh] backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="animate-rise w-full max-w-xl overflow-hidden border border-border-strong bg-popover shadow-[8px_8px_0_0_rgba(0,0,0,.35)]"
        role="dialog"
        aria-modal="true"
        aria-label="Quick navigation"
      >
        <div className="flex items-center gap-3 border-b border-border px-4">
          <Search size={16} className="shrink-0 text-signal" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search companies or jump to a module…"
            className="h-14 w-full bg-transparent text-sm outline-none placeholder:text-faint"
            onKeyDown={(e) => {
              if (e.key === 'Escape') onClose();
              if (e.key === 'Enter') {
                const first = matches[0];
                go(first ? first[0] : '/company-intel');
              }
            }}
          />
          <kbd className="border border-border px-1.5 py-1 font-mono text-[0.65rem] text-faint">ESC</kbd>
        </div>

        <div className="border-b border-border px-4 py-2">
          <p className="eyebrow">Modules · {matches.length}</p>
        </div>
        <ul className="max-h-[45vh] overflow-y-auto p-2">
          {matches.map(([to, label, Icon]) => (
            <li key={to}>
              <button
                className="flex w-full items-center gap-3 px-3 py-3 text-left transition-colors hover:bg-surface-2"
                onClick={() => go(to)}
              >
                <Icon size={15} className="shrink-0 text-faint" />
                <span className="min-w-0 flex-1 truncate text-sm">{label}</span>
                <ArrowUpRight size={13} className="shrink-0 text-faint" />
              </button>
            </li>
          ))}
        </ul>

        {companies.length > 0 && (
          <>
            <div className="border-b border-border px-4 py-2">
              <p className="eyebrow">Company dossiers · {companies.length}</p>
            </div>
            <ul className="max-h-[35vh] overflow-y-auto p-2">
              {companies.map((c: any) => (
                <li key={c.company}>
                  <button className="flex w-full items-center gap-3 px-3 py-3 text-left transition-colors hover:bg-surface-2" onClick={() => go('/company-intel')}>
                    <Radar size={15} className="shrink-0 text-faint" />
                    <span className="min-w-0 flex-1 truncate text-sm">{c.company}</span>
                    <small
                      className={`inline-flex h-6 shrink-0 items-center border px-2 font-mono text-[0.62rem] tracking-[0.12em] uppercase ${
                        c.mode === 'llm-research' ? 'border-signal/40 text-signal' : 'border-border-strong text-muted-foreground'
                      }`}
                    >
                      {c.mode === 'llm-research' ? 'verified' : 'snapshot'}
                    </small>
                    <ArrowUpRight size={13} className="shrink-0 text-faint" />
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        <footer className="flex flex-wrap gap-x-4 gap-y-1 border-t border-border px-4 py-3 text-[0.68rem] text-faint">
          <span>
            <kbd className="font-mono">↵</kbd> open first match
          </span>
          <span>
            <kbd className="font-mono">⌘K</kbd> toggle palette
          </span>
          <span>
            <kbd className="font-mono">ESC</kbd> close
          </span>
        </footer>
      </section>
    </div>
  );
}

function collectionMatches(q: string) {
  return MODULES.some(([, label]) => label.toLowerCase().includes(q.trim().toLowerCase()));
}
