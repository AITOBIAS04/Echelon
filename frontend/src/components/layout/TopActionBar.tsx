import { useLocation } from 'react-router-dom';
import { useTopActionBarActions } from '../../contexts/TopActionBarActionsContext';

interface ActionButton {
  label: string;
  icon?: string;
  kind?: 'primary' | 'warn' | 'pill';
  action?: string;
}

interface PageConfig {
  name: string;
  buttons: ActionButton[];
}

const TOP_ACTIONS: Record<string, PageConfig> = {
  '/marketplace': {
    name: 'Marketplace',
    buttons: [
      { label: 'Live', icon: '🟢', kind: 'primary', action: 'onLive' },
      { label: 'Alert', icon: '🔔', action: 'onAlert' },
      { label: 'Compare', icon: '⚖️', action: 'onCompare' },
      { label: 'New Timeline', icon: '➕', kind: 'primary', action: 'onNewTimeline' },
    ],
  },
  '/analytics': {
    name: 'Analytics',
    buttons: [
      { label: 'Alert', icon: '🔔', action: 'onAlert' },
      { label: 'Compare', icon: '⚖️', action: 'onCompare' },
      { label: 'Settings', icon: '⚙️', action: 'openShellSettings' },
    ],
  },
  '/portfolio': {
    name: 'Portfolio',
    buttons: [
      { label: 'New Position', icon: '➕', kind: 'primary', action: 'newPosition' },
    ],
  },
  '/rlmf': {
    name: 'RLMF',
    buttons: [
      { label: 'Market View', icon: '📈', action: 'marketView' },
      { label: 'Robotics View', icon: '🤖', action: 'roboticsView' },
      { label: 'Mode 0: Deterministic | Conf: 0.98', kind: 'pill' },
    ],
  },
  '/vrf': {
    name: 'VRF',
    buttons: [
      { label: 'Live', icon: '🟢', kind: 'primary', action: 'onLive' },
      { label: 'Refresh', icon: '⟳', kind: 'primary', action: 'onRefresh' },
    ],
  },
  '/agents': {
    name: 'Agents',
    buttons: [
      { label: 'Agent Roster', icon: '🧬', action: 'agentRoster' },
      { label: 'Global Intelligence', icon: '🌐', action: 'globalIntel' },
      { label: 'Search', icon: '🔎', action: 'agentSearch' },
      { label: '+ Deploy Agent', icon: '➕', kind: 'primary', action: 'deployAgent' },
    ],
  },
  '/agents/breach': {
    name: 'Breach Console',
    buttons: [],
  },
  '/agents/export': {
    name: 'Export Console',
    buttons: [],
  },
};

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
function getActionHandler(action: string, registeredActions: ReturnType<typeof useTopActionBarActions>['actions']): (() => void) | undefined {
  return registeredActions[action];
}

export function TopActionBar() {
  const location = useLocation();
  const config = resolveConfig(location.pathname);
  const { actions } = useTopActionBarActions();

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
        {config.buttons.map((btn) => {
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

          return (
            <button
              key={btn.label}
              onClick={() => {
                const handler = btn.action ? getActionHandler(btn.action, actions) : undefined;
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
                    ? 'border-[rgba(59,130,246,0.35)] bg-[rgba(59,130,246,0.1)] text-status-info hover:bg-[rgba(59,130,246,0.18)] hover:-translate-y-px'
                    : btn.kind === 'warn'
                    ? 'border-[rgba(250,204,21,0.35)] bg-[rgba(250,204,21,0.1)] text-status-warning hover:bg-[rgba(250,204,21,0.18)] hover:-translate-y-px'
                    : 'border-terminal-border bg-terminal-card text-terminal-text-secondary hover:text-terminal-text hover:border-terminal-text-muted hover:bg-[#1A1D21] hover:-translate-y-px'
                }`}
            >
              {btn.icon && <span>{btn.icon}</span>}
              <span>{btn.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
