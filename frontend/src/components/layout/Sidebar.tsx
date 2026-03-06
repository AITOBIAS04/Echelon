import React, { useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  BarChart3,
  Briefcase,
  Cpu,
  ShieldCheck,
  Users,
  AlertTriangle,
  Search,
  List,
  Plus,
  Radio,
  Home,
  X,
  Globe,
  Award,
  Boxes,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  matchPrefixes?: string[];
}

interface SubNavItem {
  path: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
}

interface SidebarProps {
  /** Whether the mobile drawer is open */
  mobileOpen?: boolean;
  /** Callback to close the mobile drawer */
  onMobileClose?: () => void;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/home', label: 'Dashboard', icon: Home },
  { path: '/theatres', label: 'Theatres', icon: LayoutDashboard, matchPrefixes: ['/theatres', '/theatre/'] },
  { path: '/fleet', label: 'Fleet', icon: Users, matchPrefixes: ['/fleet'] },
  { path: '/investigation', label: 'Investigations', icon: Search, matchPrefixes: ['/investigation'] },
  { path: '/paradox-console', label: 'Paradox Console', icon: AlertTriangle },
  { path: '/world-monitor', label: 'World Monitor', icon: Globe },
  { path: '/signal-map', label: 'Signal Map', icon: Radio },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/certificates', label: 'Certificates', icon: Award },
  { path: '/rlmf', label: 'RLMF Exports', icon: Cpu },
  { path: '/verify', label: 'Verify', icon: ShieldCheck },
  { path: '/scenario-packs', label: 'Scenario Packs', icon: Boxes },
];

// Investigation keeps a subnav for its own sub-pages (Active + Create).
// Signal Feed moved to top-level /signal-map; /agents/export moved to RLMF surface.
const INVESTIGATION_SUBNAV: SubNavItem[] = [
  { path: '/investigation', label: 'Active', icon: List },
  { path: '/investigation/create', label: 'Create', icon: Plus },
];

/**
 * Shared navigation content rendered in both desktop and mobile sidebar
 */
function NavContent({
  isExpanded,
  isActive,
  isInvestigationSection,
  location,
  onLinkClick,
}: {
  isExpanded: boolean;
  isActive: (item: NavItem) => boolean;
  isInvestigationSection: boolean;
  location: { pathname: string };
  onLinkClick?: () => void;
}) {
  const NavIcon = ({ item, className }: { item: NavItem; className?: string }) => {
    const Icon = item.icon;
    return <Icon className={className} />;
  };

  return (
    <>
      {/* Brand */}
      <div className={clsx(
        "flex items-center px-3 py-2 border border-terminal-border rounded-lg transition-all duration-300",
        "bg-gradient-to-r from-echelon-cyan/[0.06] to-transparent",
        isExpanded ? "justify-start gap-2.5 mx-2" : "justify-center mx-1.5"
      )}
        style={{ boxShadow: '0 0 20px rgba(34,211,238,0.10)' }}
      >
        {isExpanded ? (
          <span className="font-extrabold tracking-[0.14em] text-sm text-terminal-text whitespace-nowrap">
            ECHELON
          </span>
        ) : (
          <span className="w-8 h-8 rounded-lg bg-echelon-cyan/[0.12] border border-echelon-cyan/25 flex items-center justify-center font-extrabold tracking-[0.14em] text-sm text-terminal-text shadow-glow-cyan">
            E
          </span>
        )}
      </div>

      {/* Separator */}
      <div className="h-px bg-terminal-border/40 mx-3 my-1" />

      {/* Nav group */}
      <nav className={clsx(
        "flex flex-col gap-1 transition-all duration-300",
        isExpanded ? "px-2 mt-1" : "px-1.5 mt-0"
      )}>
        {isExpanded && (
          <span className="text-[10px] tracking-[0.08em] uppercase text-terminal-text-muted px-2 mt-1 mb-1">
            Console
          </span>
        )}

        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onLinkClick}
              className={clsx(
                'flex items-center gap-2.5 py-2.5 rounded-r-lg text-xs font-semibold transition-all duration-200 select-none',
                isExpanded ? 'px-3' : 'px-2.5 justify-center',
                active
                  ? 'border-l-[3px] border-l-echelon-cyan bg-echelon-cyan/[0.10] text-terminal-text'
                  : 'border-l-[3px] border-l-transparent text-terminal-text-secondary hover:bg-terminal-card hover:text-terminal-text'
              )}
            >
              {isExpanded ? (
                <>
                  <NavIcon item={item} className="w-4 h-4 flex-shrink-0" />
                  <span className="whitespace-nowrap">{item.label}</span>
                </>
              ) : (
                <div className={clsx(
                  'p-1.5 rounded-lg transition-all duration-200',
                  active && 'ring-1 ring-echelon-cyan/25'
                )}>
                  <NavIcon item={item} className="w-4 h-4" />
                </div>
              )}
            </NavLink>
          );
        })}

        {/* Investigation subnav — only shown when expanded and in section */}
        {isExpanded && isInvestigationSection && (
          <>
            <div className="h-px bg-terminal-border/40 mx-3 my-1" />
            <div className="mt-1 flex flex-col gap-1 pl-2 border-l border-terminal-border ml-3">
              {INVESTIGATION_SUBNAV.map((item) => {
                const active = location.pathname === item.path;
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onLinkClick}
                    className={clsx(
                      'flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium transition-all duration-200',
                      active
                        ? 'text-status-info bg-status-info/10'
                        : 'text-terminal-text-muted hover:text-terminal-text-secondary hover:bg-terminal-panel'
                    )}
                  >
                    {Icon && <Icon className="w-3.5 h-3.5 flex-shrink-0" />}
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          </>
        )}
      </nav>
    </>
  );
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);
  const collapseTimeoutRef = React.useRef<number | null>(null);

  const isActive = useCallback((item: NavItem) => {
    if (location.pathname === item.path) return true;
    if (item.matchPrefixes) {
      return item.matchPrefixes.some((p) => location.pathname.startsWith(p));
    }
    return false;
  }, [location.pathname]);

  const isInvestigationSection = location.pathname.startsWith('/investigation');

  const handleMouseEnter = useCallback(() => {
    if (collapseTimeoutRef.current) {
      window.clearTimeout(collapseTimeoutRef.current);
      collapseTimeoutRef.current = null;
    }
    setIsExpanded(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    collapseTimeoutRef.current = window.setTimeout(() => {
      setIsExpanded(false);
    }, 250);
  }, []);

  return (
    <>
      {/* ═══════════ DESKTOP SIDEBAR (md and above) ═══════════ */}
      <aside
        className="hidden md:flex h-full flex-shrink-0 bg-terminal-panel border-r border-terminal-border flex-col py-3 gap-2 overflow-hidden transition-all duration-300 ease-out"
        style={{
          width: isExpanded ? '180px' : '64px',
          boxShadow: 'inset -1px 0 0 rgba(255,255,255,0.04), 2px 0 8px rgba(0,0,0,0.3)',
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <NavContent
          isExpanded={isExpanded}
          isActive={isActive}
          isInvestigationSection={isInvestigationSection}
          location={location}
        />
      </aside>

      {/* ═══════════ MOBILE DRAWER (below md) ═══════════ */}
      {/* Overlay */}
      <div
        className={clsx(
          'md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300',
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={onMobileClose}
      />

      {/* Drawer */}
      <aside
        className={clsx(
          'md:hidden fixed inset-y-0 left-0 z-50 w-[240px] bg-terminal-panel border-r border-terminal-border flex flex-col py-3 gap-2 overflow-y-auto transition-transform duration-300 ease-out',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        style={{ boxShadow: mobileOpen ? '4px 0 16px rgba(0,0,0,0.5)' : 'none' }}
      >
        {/* Close button */}
        <div className="flex items-center justify-between px-3 mb-1">
          <span className="font-extrabold tracking-[0.14em] text-sm text-terminal-text">ECHELON</span>
          <button
            onClick={onMobileClose}
            className="p-1.5 rounded-lg text-terminal-text-muted hover:text-terminal-text hover:bg-terminal-card transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Separator */}
        <div className="h-px bg-terminal-border/40 mx-3 my-1" />

        <NavContent
          isExpanded={true}
          isActive={isActive}
          isInvestigationSection={isInvestigationSection}
          onLinkClick={onMobileClose}
          location={location}
        />
      </aside>
    </>
  );
}

export default Sidebar;
