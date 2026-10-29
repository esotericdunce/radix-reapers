import { useEffect, useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AppHeader } from './components/neo/AppHeader';
import { Overview } from './pages/Overview';
import { JDAnalytics } from './pages/JDAnalytics';
import { ResumeParser } from './pages/ResumeParser';
import { ProfileBuilder } from './pages/ProfileBuilder';
import { TalentCheck } from './pages/TalentCheck';
import { SkillMatching } from './pages/SkillMatching';
import { CompanyIntel } from './pages/CompanyIntel';
import { HiringCommittee } from './pages/HiringCommittee';
import { InterviewArena } from './pages/InterviewArena';
import { CareerRadar } from './pages/CareerRadar';
import { CommandPalette } from './pages/CommandPalette';

export default function App() {
  const [palette, setPalette] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPalette((v) => !v);
      } else if (e.key === 'Escape' && document.querySelector('.cmdk-backdrop')) setPalette(false);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  return (
    <div className="shell min-h-screen hairline-grid">
      <AppHeader onOpenSearch={() => setPalette((v) => !v)} />
      <main className="app-page mx-auto w-full max-w-7xl px-4 pt-8 pb-10 sm:px-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/jd-analytics" element={<JDAnalytics />} />
          <Route path="/resume-parser" element={<ResumeParser />} />
          <Route path="/profile" element={<ProfileBuilder />} />
          <Route path="/talent-check" element={<TalentCheck />} />
          <Route path="/skill-matching" element={<SkillMatching />} />
          <Route path="/company-intel" element={<CompanyIntel />} />
          <Route path="/hiring-committee" element={<HiringCommittee />} />
          <Route path="/interview-arena" element={<InterviewArena />} />
          <Route path="/career-radar" element={<CareerRadar />} />
        </Routes>
        <footer className="mt-14 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-5 font-mono text-[0.68rem] tracking-[0.1em] text-faint uppercase">
          <span>
            RADIX TalentMatch <span className="px-1">•</span> Local-first skills intelligence
          </span>
          <span>Heuristic analysis · No paid AI required</span>
        </footer>
      </main>
      <CommandPalette open={palette} onClose={() => setPalette(false)} />
    </div>
  );
}
