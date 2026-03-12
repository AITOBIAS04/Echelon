import type { ComponentType } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  ArrowDownToLine,
  BarChart3,
  Box,
  Clock3,
  CreditCard,
  GitBranch,
  Hash,
  Home,
  LayoutGrid,
  Mountain,
  Radar,
  Shield,
  ShieldCheck,
  SlidersHorizontal,
  SquareStack,
  X,
} from 'lucide-react';

interface SidebarProps {
  collapsed?: boolean;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  matchPrefixes?: string[];
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

/* Standalone top link — no group header */
const HOME_LINK: NavItem = { path: '/', label: 'Home', icon: Home };

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Command',
    items: [
      { path: '/home', label: 'Mission Control', icon: LayoutGrid },
      { path: '/theatres', label: 'Theatres', icon: Clock3, matchPrefixes: ['/theatres', '/theatre/'] },
      { path: '/portfolio', label: 'Positions', icon: Box },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/world-monitor', label: 'WorldMonitor', icon: Radar, matchPrefixes: ['/world-monitor'] },
      { path: '/signal-map', label: 'Signal Map', icon: Mountain },
      { path: '/investigation', label: 'Investigations', icon: Hash, matchPrefixes: ['/investigation'] },
    ],
  },
  {
    label: 'Operations',
    items: [
      { path: '/fleet', label: 'Fleet', icon: SlidersHorizontal, matchPrefixes: ['/fleet'] },
      { path: '/paradox-console', label: 'Paradox Console', icon: GitBranch },
      { path: '/scenario-packs', label: 'Scenario Packs', icon: SquareStack },
    ],
  },
  {
    label: 'Verification',
    items: [
      { path: '/verify', label: 'Verify', icon: ShieldCheck },
      { path: '/certificates', label: 'Certificates', icon: CreditCard },
      { path: '/vrf', label: 'VRF', icon: Shield },
      { path: '/rlmf', label: 'RLMF Exports', icon: ArrowDownToLine },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
];

function NavGroups({
  collapsed,
  onLinkClick,
}: {
  collapsed: boolean;
  onLinkClick?: () => void;
}) {
  const location = useLocation();

  const isActive = (item: NavItem) => {
    if (location.pathname === item.path) return true;
    return item.matchPrefixes?.some((prefix) => location.pathname.startsWith(prefix)) ?? false;
  };

  const renderLink = (item: NavItem) => {
    const active = isActive(item);
    const Icon = item.icon;
    return (
      <NavLink
        key={item.path}
        to={item.path}
        onClick={onLinkClick}
        className={clsx(
          'relative mx-2 my-px flex h-9 items-center rounded-md text-[13px] font-medium transition-all duration-100',
          collapsed ? 'justify-center px-0' : 'gap-3 px-5',
          active
            ? 'bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
            : 'text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
        )}
        title={collapsed ? item.label : undefined}
      >
        {active ? (
          <span className="absolute inset-y-[6px] left-0 w-[3px] rounded-r-[2px] bg-[var(--e-purple-500)]" />
        ) : null}
        <span className={clsx('flex h-5 w-5 items-center justify-center', active ? 'opacity-100' : 'opacity-70')}>
          <Icon className="h-4 w-4" />
        </span>
        {!collapsed ? <span className="truncate">{item.label}</span> : null}
      </NavLink>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto py-3">
      {/* Standalone Home link */}
      <div className="mb-1 pb-1">
        {renderLink(HOME_LINK)}
      </div>

      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="mb-1">
          <div
            className={clsx(
              'overflow-hidden px-5 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--e-text-muted)]',
              collapsed && 'px-4 text-[0px] after:mx-auto after:block after:h-px after:w-4 after:bg-[var(--e-border-primary)] after:content-[\'\']',
            )}
          >
            {!collapsed ? group.label : null}
          </div>
          {group.items.map(renderLink)}
        </div>
      ))}
    </div>
  );
}

export function Sidebar({
  collapsed = false,
  mobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  const desktopWidth = collapsed ? '4rem' : '15rem';

  return (
    <>
      <aside
        className="fixed top-14 bottom-0 left-0 z-20 hidden border-r border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-xs)] transition-[width] duration-300 ease-out md:flex md:flex-col"
        style={{ width: desktopWidth }}
      >
        <NavGroups collapsed={collapsed} />
      </aside>

      <div
        className={clsx(
          'fixed inset-0 z-40 bg-[color:oklch(0.20_0.01_265_/_0.35)] backdrop-blur-sm transition-opacity duration-300 md:hidden',
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        )}
        onClick={onMobileClose}
      />

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-[var(--e-border-primary)] bg-[var(--e-bg-card)] shadow-[var(--e-shadow-md)] transition-transform duration-300 ease-out md:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-[var(--e-border-primary)] px-4">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--e-purple-500)] font-mono text-sm font-semibold text-[var(--e-text-inverse)]">
              E
            </span>
            <span className="text-[17px] font-bold tracking-[-0.02em] text-[var(--e-text-primary)]">Echelon</span>
          </div>
          <button
            type="button"
            onClick={onMobileClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-secondary)]"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <NavGroups collapsed={false} onLinkClick={onMobileClose} />
      </aside>
    </>
  );
}

export default Sidebar;
