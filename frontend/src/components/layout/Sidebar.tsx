import React, { useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { 
  LayoutDashboard, 
  BarChart3, 
  Briefcase, 
  Cpu, 
  Shield, 
  Users,
  AlertTriangle,
  Download
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  matchPrefixes?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { path: '/marketplace', label: 'Marketplace', icon: LayoutDashboard },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/rlmf', label: 'RLMF', icon: Cpu },
  { path: '/vrf', label: 'VRF', icon: Shield },
  { path: '/agents', label: 'Agents', icon: Users, matchPrefixes: ['/agents', '/agent/'] },
];

const AGENTS_SUBNAV: NavItem[] = [
  { path: '/agents/breach', label: 'Breach Console', icon: AlertTriangle },
  { path: '/agents/export', label: 'Export Console', icon: Download },
];

export function Sidebar() {
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

  const isAgentsSection = location.pathname.startsWith('/agents') || location.pathname.startsWith('/agent/');

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

  const NavIcon = ({ item, className }: { item: NavItem; className?: string }) => {
    const Icon = item.icon;
    return <Icon className={className} />;
  };

  return (
    <aside 
      className="h-full flex-shrink-0 bg-[#0B0C0E] border-r border-[#26292E] flex flex-col py-3 gap-2 overflow-hidden transition-all duration-300 ease-out"
      style={{ 
        width: isExpanded ? '180px' : '64px',
        marginLeft: isExpanded ? '0' : '0'
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Brand */}
      <div className={clsx(
        "flex items-center px-3 py-2 border border-[#26292E] rounded-lg bg-[rgba(18,20,23,0.55)] transition-all duration-300",
        isExpanded ? "justify-start gap-2.5" : "justify-center"
      )}>
        <span className="font-extrabold tracking-[0.14em] text-sm text-[#F1F5F9] whitespace-nowrap">
          {isExpanded && "ECHELON"}
        </span>
        {!isExpanded && (
          <span className="font-extrabold tracking-[0.14em] text-sm text-[#F1F5F9]">E</span>
        )}
      </div>

      {/* Nav group */}
      <nav className={clsx(
        "flex flex-col gap-1 transition-all duration-300",
        isExpanded ? "px-2 mt-1" : "px-1.5 mt-0"
      )}>
        {isExpanded && (
          <span className="text-[10px] tracking-[0.08em] uppercase text-[#64748B] px-2 mt-1 mb-1">
            Console
          </span>
        )}

        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-2.5 px-2.5 py-2.5 rounded-lg border text-xs font-semibold transition-all duration-200 select-none',
                active
                  ? 'bg-[rgba(26,29,33,0.9)] border-[#26292E] text-[#F1F5F9]'
                  : 'border-transparent text-[#94A3B8] hover:bg-[#151719] hover:border-[#26292E] hover:text-[#F1F5F9]'
              )}
              style={{ justifyContent: isExpanded ? 'flex-start' : 'center' }}
            >
              <span
                className={clsx(
                  'w-1.5 h-1.5 rounded-full flex-shrink-0 transition-all duration-200',
                  active
                    ? 'bg-[#3B82F6] shadow-[0_0_8px_rgba(59,130,246,0.3)]'
                    : 'bg-[#64748B]'
                )}
              />
              {isExpanded && <span className="whitespace-nowrap">{item.label}</span>}
              {!isExpanded && (
                <div className="relative">
                  <NavIcon item={item} className="w-4 h-4" />
                  {active && (
                    <span className="absolute -right-1 -top-1 w-1.5 h-1.5 rounded-full bg-[#3B82F6]" />
                  )}
                </div>
              )}
            </NavLink>
          );
        })}

        {/* Agents subnav — visible when Agents section is active */}
        {isAgentsSection && (
          <div className={clsx(
            "flex flex-col gap-1 transition-all duration-300 overflow-hidden",
            isExpanded ? "pl-3 mt-1" : "pl-0 mt-0"
          )}>
            {isExpanded && (
              <span className="text-[10px] tracking-[0.08em] uppercase text-[#64748B] mt-2 mb-1">
                Agents
              </span>
            )}
            {AGENTS_SUBNAV.map((sub) => {
              const subActive = location.pathname === sub.path;
              return (
                <NavLink
                  key={sub.path}
                  to={sub.path}
                  className={clsx(
                    'px-2.5 py-2 rounded-lg border text-[11px] font-semibold transition-all duration-200',
                    subActive
                      ? 'bg-[#151719] border-[#26292E] text-[#F1F5F9]'
                      : 'border-transparent text-[#94A3B8] hover:bg-[#151719] hover:border-[#26292E] hover:text-[#F1F5F9]'
                  )}
                  style={{ justifyContent: isExpanded ? 'flex-start' : 'center' }}
                >
                  {isExpanded ? (
                    <>
                      <sub.icon className="w-3.5 h-3.5" />
                      <span>{sub.label}</span>
                    </>
                  ) : (
                    <sub.icon className="w-4 h-4" />
                  )}
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
