import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';

interface NavItem {
  path: string;
  label: string;
  /** Also match these path prefixes as "active" */
  matchPrefixes?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { path: '/marketplace', label: 'Marketplace' },
  { path: '/analytics', label: 'Analytics' },
  { path: '/portfolio', label: 'Portfolio' },
  { path: '/rlmf', label: 'RLMF' },
  { path: '/vrf', label: 'VRF' },
  { path: '/agents', label: 'Agents', matchPrefixes: ['/agents', '/agent/'] },
];

const AGENTS_SUBNAV = [
  { path: '/agents/breach', label: 'Breach Console' },
  { path: '/agents/export', label: 'Export Console' },
];

export function Sidebar() {
  const location = useLocation();

  const isActive = (item: NavItem) => {
    if (location.pathname === item.path) return true;
    if (item.matchPrefixes) {
      return item.matchPrefixes.some((p) => location.pathname.startsWith(p));
    }
    return false;
  };

  const isAgentsSection =
    location.pathname.startsWith('/agents') || location.pathname.startsWith('/agent/');

  return (
    <aside className="w-[240px] flex-shrink-0 bg-terminal-panel border-r border-terminal-border flex flex-col py-3.5 px-3 gap-3 overflow-y-auto">
      {/* Brand */}
      <div className="flex items-center justify-between px-2.5 py-2 border border-terminal-border rounded-[10px] bg-[rgba(18,20,23,0.55)]">
        <span className="font-extrabold tracking-[0.14em] text-sm text-terminal-text">
          ECHELON
        </span>
        <span className="text-[10px] font-mono text-terminal-text-muted border border-terminal-border px-1.5 py-0.5 rounded-md bg-[#0B0C0E]">
          UNIFIED
        </span>
      </div>

      {/* Nav group */}
      <nav className="flex flex-col gap-1.5">
        <span className="text-[10px] tracking-[0.08em] uppercase text-terminal-text-muted px-2 mt-1.5">
          Console
        </span>

        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-2.5 px-2.5 py-[9px] rounded-[10px] border text-xs font-semibold transition-all duration-150 select-none',
                active
                  ? 'bg-[rgba(26,29,33,0.9)] border-terminal-border text-terminal-text'
                  : 'border-transparent text-terminal-text-secondary hover:bg-terminal-card hover:border-terminal-border hover:text-terminal-text'
              )}
            >
              <span
                className={clsx(
                  'w-[7px] h-[7px] rounded-full flex-shrink-0',
                  active
                    ? 'bg-status-info shadow-[0_0_10px_rgba(59,130,246,0.25)]'
                    : 'bg-terminal-text-muted'
                )}
              />
              {item.label}
            </NavLink>
          );
        })}

        {/* Agents subnav — visible when Agents section is active */}
        {isAgentsSection && (
          <div className="flex flex-col gap-1 pl-[22px] -mt-1">
            <span className="text-[10px] tracking-[0.08em] uppercase text-terminal-text-muted mt-2.5 mb-0.5">
              Agents
            </span>
            {AGENTS_SUBNAV.map((sub) => {
              const subActive = location.pathname === sub.path;
              return (
                <NavLink
                  key={sub.path}
                  to={sub.path}
                  className={clsx(
                    'px-2.5 py-2 rounded-[10px] border text-[11px] font-semibold transition-all duration-150',
                    subActive
                      ? 'bg-terminal-card border-terminal-border text-terminal-text'
                      : 'border-transparent text-terminal-text-secondary hover:bg-terminal-card hover:border-terminal-border hover:text-terminal-text'
                  )}
                >
                  {sub.label}
                </NavLink>
              );
            })}
          </div>
        )}
      </nav>
    </aside>
  );
}

export default Sidebar;
