import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTopActionBarActions, type TopActionBarActions } from '../../contexts/TopActionBarActionsContext';
import { useAgentsUi, type AgentsTab } from '../../contexts/AgentsUiContext';
import {
  Radio,
  Bell,
  GitCompare,
  Plus,
  BarChart3,
  Cpu,
  RefreshCw,
  Users,
  Globe,
  Search,
  Settings
} from 'lucide-react';
import { clsx } from 'clsx';

interface ActionButton {
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  kind?: 'primary' | 'warn' | 'pill';
  action?: string;
  isTab?: boolean;
  tabValue?: AgentsTab;
}

interface PageConfig {
  name: string;
  buttons: ActionButton[];
}

const TOP_ACTIONS: Record<string, PageConfig> = {
  '/marketplace': {
    name: 'Marketplace',
    buttons: [
      { label: 'Live', icon: Radio, kind: 'primary', action: 'onLive' },
      { label: 'Alert', icon: Bell, action: 'onAlert' },
      { label: 'Compare', icon: GitCompare, action: 'onCompare' },
      { label: 'New Timeline', icon: Plus, kind: 'primary', action: 'onNewTimeline' },
    ],
  },
  '/analytics': {
    name: 'Analytics',
    buttons: [
      { label: 'Alert', icon: Bell, action: 'onAlert' },
      { label: 'Compare', icon: GitCompare, action: 'onCompare' },
      { label: 'Settings', icon: Settings, action: 'openShellSettings' },
    ],
  },
  '/portfolio': {
    name: 'Portfolio',
    buttons: [
      { label: 'New Position', icon: Plus, kind: 'primary', action: 'newPosition' },
    ],
  },
  '/rlmf': {
    name: 'RLMF',
    buttons: [
      { label: 'Market View', icon: BarChart3, action: 'marketView' },
      { label: 'Robotics View', icon: Cpu, action: 'roboticsView' },
      { label: 'Mode 0: Deterministic | Conf: 0.98', kind: 'pill' },
    ],
  },
  '/vrf': {
    name: 'VRF',
    buttons: [
      { label: 'Live', icon: Radio, kind: 'primary', action: 'onLive' },
      { label: 'Refresh', icon: RefreshCw, kind: 'primary', action: 'onRefresh' },
    ],
  },
  '/agents': {
    name: 'Agents',
    buttons: [
      { label: 'Agent Roster', icon: Users, isTab: true, tabValue: 'roster' },
      { label: 'Global Intelligence', icon: Globe, isTab: true, tabValue: 'intel' },
      { label: 'Search', icon: Search, action: 'agentSearch' },
      { label: 'Deploy Agent', icon: Plus, kind: 'primary', action: 'deployAgent' },
    ],
  },
};

/** Routes where Live/Alert/Compare buttons should be hidden */
const HIDE_LIVE_ALERT_COMPARE_ROUTES = [
  '/agents/breach',
  '/agents/export',
  '/analytics',
];

/** Check if current route should hide Live/Alert/Compare buttons */
function shouldHideLiveAlertCompare(pathname: string): boolean {
  if (HIDE_LIVE_ALERT_COMPARE_ROUTES.includes(pathname)) return true;
  if (pathname.startsWith('/launchpad')) return true;
  return false;
}

/** Resolve a pathname to the best matching config key */
function resolveConfig(pathname: string): PageConfig {
  // Exact match
  if (TOP_ACTIONS[pathname]) return TOP_ACTIONS[pathname];

  // Prefix match for detail routes (e.g. /agent/:id → Agents)
  if (pathname.startsWith('/agents')) return TOP_ACTIONS['/agents'];
  if (pathname.startsWith('/agent/')) return TOP_ACTIONS['/agents'];
  if (pathname.startsWith('/timeline/')) return { name: 'Timeline', buttons: [] };

  // Fallback
  return TOP_ACTIONS['/marketplace'];
}

/**
 * Get action handler from registered actions
 */
function getActionHandler(action: string, actionsRef: React.MutableRefObject<TopActionBarActions>): (() => void) | undefined {
  return actionsRef.current[action];
}

export function TopActionBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const config = resolveConfig(location.pathname);
  const { actionsRef } = useTopActionBarActions();
  const { activeTab, setActiveTab } = useAgentsUi();

  // Check if this is the agents page
  const isAgentsPage = location.pathname === '/agents' || location.pathname.startsWith('/agents/');

  // Filter out Live/Alert/Compare on specific routes
  const hideLiveAlertCompare = shouldHideLiveAlertCompare(location.pathname);
  const filteredButtons = hideLiveAlertCompare
    ? config.buttons.filter(btn => btn.label !== 'Live' && btn.label !== 'Alert' && btn.label !== 'Compare')
    : config.buttons;

  return (
    <div className="h-14 flex-shrink-0 flex items-center justify-between px-4 border-b border-terminal-border bg-[rgba(18,20,23,0.65)] backdrop-blur-sm">
      {/* Page name / breadcrumb */}
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="text-xs font-extrabold tracking-[0.06em] uppercase text-terminal-text whitespace-nowrap">
          {config.name}
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        {filteredButtons.map((btn) => {
          // Tab buttons for agents page
          if (btn.isTab && isAgentsPage) {
            const isActive = activeTab === btn.tabValue;
            return (
              <button
                key={btn.label}
                onClick={() => btn.tabValue && setActiveTab(btn.tabValue)}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all duration-150 whitespace-nowrap',
                  isActive
                    ? 'border-[rgba(34,211,238,0.35)] bg-[rgba(34,211,238,0.1)] text-[#22D3EE]'
                    : 'border-[#26292E] bg-[#151719] text-[#94A3B8] hover:text-[#F1F5F9] hover:border-[#64748B] hover:bg-[#1A1D21]'
                )}
              >
                {btn.icon && React.createElement(btn.icon, { className: "w-3.5 h-3.5" })}
                <span>{btn.label}</span>
              </button>
            );
          }

          // Pill-style buttons
          if (btn.kind === 'pill') {
            return (
              <span
                key={btn.label}
                className="font-mono text-[11px] px-2.5 py-1.5 rounded-full border border-terminal-border bg-terminal-card text-terminal-text-secondary whitespace-nowrap"
              >
                {btn.label}
              </span>
            );
          }

          // Regular action buttons
          return (
            <button
              key={btn.label}
              onClick={() => {
                // Navigate to Launchpad for New Timeline
                if (btn.action === 'onNewTimeline') {
                  navigate('/launchpad');
                  return;
                }
                const handler = btn.action ? getActionHandler(btn.action, actionsRef) : undefined;
                if (handler) {
                  handler();
                } else if (btn.action === 'noop') {
                  // No-op action, do nothing
                } else {
                  // Fallback for actions without handlers
                  console.warn(`TopActionBar: No handler registered for action "${btn.action}" on page "${config.name}"`);
                }
              }}
              className={`flex items-center gap-2 px-2.5 py-[7px] rounded-[10px] border text-[11px] font-semibold transition-all duration-150 whitespace-nowrap
                ${
                  btn.kind === 'primary'
                    ? 'border-[rgba(59,130,246,0.35)] bg-[rgba(59,130,246,0.1)] text-[#3B82F6] hover:bg-[rgba(59,130,246,0.18)] hover:-translate-y-px'
                    : btn.kind === 'warn'
                    ? 'border-[rgba(250,204,21,0.35)] bg-[rgba(250,204,21,0.1)] text-[#FACC15] hover:bg-[rgba(250,204,21,0.18)] hover:-translate-y-px'
                    : 'border-[#26292E] bg-[#151719] text-[#94A3B8] hover:text-[#F1F5F9] hover:border-[#64748B] hover:bg-[#1A1D21] hover:-translate-y-px'
                }`}
            >
              {btn.icon && React.createElement(btn.icon, { className: "w-3.5 h-3.5" })}
              <span>{btn.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
