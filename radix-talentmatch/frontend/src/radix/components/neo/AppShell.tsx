import { useEffect, useState, type ReactNode } from "react";
import { Compass, LayoutDashboard, Menu, Mic, Moon, Search, ShieldCheck, Sun, Users, X } from "lucide-react";
import { Link, useLocation } from "../../router";
import { useTheme } from "../../hooks/use-theme";
import { DEMO_MODE } from "../../services/api";
import { CommandPalette } from "../../pages/CommandPalette";

const JOURNEY = [
  { to: "/jd-analytics", label: "Read the role" },
  { to: "/resume-parser", label: "Read the resume" },
  { to: "/profile", label: "Shape the profile" },
  { to: "/talent-check", label: "Check readiness" },
  { to: "/skill-matching", label: "Measure the fit" },
];
const LABS = [
  { to: "/company-intel", label: "Company Intel", Icon: ShieldCheck },
  { to: "/hiring-committee", label: "Hiring Committee", Icon: Users },
  { to: "/interview-arena", label: "Mock Interview", Icon: Mic },
  { to: "/career-radar", label: "Career Radar", Icon: Compass },
];

function Nav({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const active = (to: string) => (to === "/" ? pathname === "/" : pathname.startsWith(to));
  return (
    <>
      <div className="nav-group">
        <Link to="/" className="nav-link" data-active={active("/")} onClick={onNavigate}>
          <LayoutDashboard /> Overview
        </Link>
      </div>
      <div className="nav-group">
        <div className="nav-group-label">Journey</div>
        {JOURNEY.map((n, i) => (
          <Link key={n.to} to={n.to} className="nav-link" data-active={active(n.to)} onClick={onNavigate}>
            <span className="nav-num">0{i + 1}</span>
            {n.label}
          </Link>
        ))}
      </div>
      <div className="nav-group">
        <div className="nav-group-label">Labs</div>
        {LABS.map(({ to, label, Icon }) => (
          <Link key={to} to={to} className="nav-link" data-active={active(to)} onClick={onNavigate}>
            <Icon /> {label}
          </Link>
        ))}
      </div>
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const { theme, toggle } = useTheme();
  const [palette, setPalette] = useState(false);
  const [drawer, setDrawer] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((v) => !v);
      } else if (e.key === "Escape") setPalette(false);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  useEffect(() => setDrawer(false), [pathname]);

  const Brand = (
    <Link to="/" className="brand">
      <span className="brand-mark">RADIX</span>
      <span className="brand-dot" />
    </Link>
  );

  return (
    <div className="shell min-h-screen hairline-grid">
      <header className="topbar">
        {Brand}
        <div className="flex items-center gap-2">
          <button className="icon-btn" aria-label="Search" onClick={() => setPalette(true)}>
            <Search size={15} />
          </button>
          <button className="icon-btn" aria-label={drawer ? "Close menu" : "Open menu"} onClick={() => setDrawer((v) => !v)}>
            {drawer ? <X size={15} /> : <Menu size={15} />}
          </button>
        </div>
      </header>
      {drawer && (
        <div className="mobile-drawer">
          <Nav pathname={pathname} onNavigate={() => setDrawer(false)} />
        </div>
      )}
      <div className="shell-grid">
        <aside className="sidebar">
          {Brand}
          <Nav pathname={pathname} />
          <div className="sidebar-foot">
            <button className="search-trigger" onClick={() => setPalette(true)}>
              <Search size={14} /> Search
              <kbd>⌘K</kbd>
            </button>
            <div className="mode-note">
              <span>
                <i />
                {DEMO_MODE ? "Demo data" : "Live API"}
              </span>
              <button className="icon-btn" onClick={toggle} aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
                {theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
              </button>
            </div>
          </div>
        </aside>
        <main className="shell-main">
          <div key={pathname} className="app-page shell-content">
            {children}
          </div>
        </main>
      </div>
      <CommandPalette open={palette} onClose={() => setPalette(false)} />
    </div>
  );
}
