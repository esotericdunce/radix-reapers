import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Moon, Search, Sun } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useTheme } from '../../hooks/use-theme';

const NAV: { to: string; label: string; exact?: boolean }[] = [
  { to: '/', label: 'Overview', exact: true },
  { to: '/jd-analytics', label: 'JD Analytics' },
  { to: '/resume-parser', label: 'Resume' },
  { to: '/profile', label: 'Profile' },
  { to: '/talent-check', label: 'Talent Check' },
  { to: '/skill-matching', label: 'Matching' },
  { to: '/company-intel', label: 'Intel Lab' },
  { to: '/hiring-committee', label: 'Committee' },
  { to: '/interview-arena', label: 'Interview' },
  { to: '/career-radar', label: 'Radar' },
];

/** Premium CRED-style sticky header: display wordmark, mono tab rail with a
 *  signal underline, quick-search palette trigger and theme toggle. */
export function AppHeader({ onOpenSearch }: { onOpenSearch: () => void }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 pb-10 backdrop-blur-xl md:pb-0">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:gap-6 sm:px-8">
        <Link to="/" className="flex shrink-0 items-baseline gap-2">
          <span className="font-display text-2xl leading-none">RADIX</span>
          <span className="eyebrow hidden sm:inline">TalentMatch</span>
        </Link>

        <nav className="no-scrollbar -mb-px hidden h-full flex-1 items-stretch gap-1 overflow-x-auto md:flex">
          {NAV.map((n) => {
            const active = n.exact ? pathname === n.to : pathname.startsWith(n.to);
            return (
              <Link
                key={n.to}
                to={n.to}
                className={cn(
                  'group relative flex items-center whitespace-nowrap px-3 font-mono text-[0.72rem] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-foreground',
                  active && '!text-foreground',
                )}
              >
                {n.label}
                <span
                  className={cn(
                    'absolute inset-x-3 bottom-0 h-[2px] bg-signal transition-transform duration-300',
                    active ? 'scale-x-100' : 'scale-x-0',
                  )}
                />
              </Link>
            );
          })}
        </nav>

        {/* Mobile: horizontally scrollable tab rail below the top row */}
        <nav className="no-scrollbar absolute inset-x-0 top-16 flex h-10 items-stretch gap-1 overflow-x-auto border-b border-border bg-background/85 px-4 backdrop-blur-xl md:hidden">
          {NAV.map((n) => {
            const active = n.exact ? pathname === n.to : pathname.startsWith(n.to);
            return (
              <Link
                key={n.to}
                to={n.to}
                className={cn(
                  'relative flex shrink-0 items-center whitespace-nowrap px-2.5 font-mono text-[0.68rem] uppercase tracking-[0.12em] text-muted-foreground',
                  active && '!text-foreground',
                )}
              >
                {n.label}
                <span
                  className={cn(
                    'absolute inset-x-2.5 bottom-0 h-[2px] bg-signal transition-transform duration-300',
                    active ? 'scale-x-100' : 'scale-x-0',
                  )}
                />
              </Link>
            );
          })}
        </nav>

        <button
          onClick={onOpenSearch}
          aria-label="Quick search modules and companies"
          className="ml-auto flex h-9 min-w-9 items-center justify-center gap-2 border border-border-strong px-2.5 text-muted-foreground transition-colors hover:border-foreground/40 hover:text-foreground sm:ml-0 sm:px-3"
        >
          <Search className="h-4 w-4" />
          <span className="hidden text-xs sm:inline">Quick search</span>
          <kbd className="hidden font-mono text-[0.62rem] sm:inline-flex">Ctrl / ⌘ K</kbd>
        </button>

        <button
          onClick={toggle}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="flex h-9 w-9 shrink-0 items-center justify-center border border-border-strong text-muted-foreground transition-all hover:text-foreground active:translate-x-px active:translate-y-px"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        <button
          onClick={() => navigate('/profile')}
          aria-label="Open Profile Builder"
          title="Open Profile Builder"
          className="hidden h-9 w-9 shrink-0 items-center justify-center border border-border-strong font-mono text-[0.65rem] uppercase text-signal transition-all hover:border-foreground/40 active:translate-x-px active:translate-y-px lg:flex"
        >
          AR
        </button>
      </div>
    </header>
  );
}
