import type { ComponentType, MutableRefObject } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Award,
  List,
  Menu,
  Plus,
} from 'lucide-react';
import { useTopActionBarActions, type TopActionBarActions } from '../../contexts/TopActionBarActionsContext';
import { useAgentsUi, type AgentsTab } from '../../contexts/AgentsUiContext';
import { useRlmfUi } from '../../contexts/RlmfUiContext';
import { useVerifyUi, type VerifyTab } from '../../contexts/VerifyUiContext';

interface ActionButton {
  label: string;
  icon?: ComponentType<{ className?: string }>;
  kind?: 'primary' | 'pill';
  action?: string;
  isTab?: boolean;
  tabValue?: AgentsTab;
  isRlmfViewTab?: boolean;
  rlmfViewValue?: 'market' | 'robotics';
  isVerifyTab?: boolean;
  verifyTabValue?: VerifyTab;
}

interface PageConfig {
  name: string;
  eyebrow?: string;
  buttons: ActionButton[];
}

interface TopActionBarProps {
  onHamburgerClick?: () => void;
}

const PAGE_CONFIGS: Array<{ match: (pathname: string) => boolean; config: PageConfig }> = [
  {
    match: (pathname) => pathname === '/home',
    config: { name: 'Dashboard', eyebrow: 'Overview', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/theatres',
    config: {
      name: 'Theatres',
      eyebrow: 'Market / Templates',
      buttons: [{ label: 'Create Theatre', icon: Plus, kind: 'primary', action: 'createTheatre' }],
    },
  },
  {
    match: (pathname) => pathname === '/theatres/create',
    config: { name: 'Create Theatre', eyebrow: 'Theatres', buttons: [] },
  },
  {
    match: (pathname) => pathname.startsWith('/theatre/'),
    config: {
      name: 'Theatre Detail',
      eyebrow: 'Theatres',
      buttons: [{ label: 'Deploy Agent', icon: Plus, kind: 'primary', action: 'deployAgent' }],
    },
  },
  {
    match: (pathname) => pathname === '/fleet' || pathname.startsWith('/fleet/'),
    config: {
      name: 'Fleet',
      eyebrow: 'Operations',
      buttons: [{ label: 'Deploy Agent', icon: Plus, kind: 'primary', action: 'deployAgent' }],
    },
  },
  {
    match: (pathname) => pathname === '/investigation' || pathname.startsWith('/investigation'),
    config: { name: 'Investigations', eyebrow: 'Intelligence', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/paradox-console',
    config: { name: 'Paradox Console', eyebrow: 'Risk / Status', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/world-monitor',
    config: { name: 'World Monitor', eyebrow: 'Intelligence', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/world-monitor/live',
    config: { name: 'Global Map', eyebrow: 'Intelligence', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/signal-map',
    config: { name: 'Signal Map', eyebrow: 'Intelligence', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/portfolio',
    config: { name: 'Portfolio', eyebrow: 'Systems', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/analytics',
    config: { name: 'Analytics', eyebrow: 'Systems', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/certificates',
    config: { name: 'Certificates', eyebrow: 'Operations', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/scenario-packs',
    config: { name: 'Scenario Packs', eyebrow: 'Alpamayo Studio', buttons: [] },
  },
  {
    match: (pathname) => pathname.startsWith('/scenario-packs/'),
    config: { name: 'Scenario Pack Detail', eyebrow: 'Alpamayo Studio', buttons: [] },
  },
  {
    match: (pathname) => pathname === '/rlmf',
    config: {
      name: 'RLMF Exports',
      eyebrow: 'Data Product',
      buttons: [],
    },
  },
  {
    match: (pathname) => pathname === '/verify',
    config: {
      name: 'Verify',
      eyebrow: 'Verification',
      buttons: [
        { label: 'My Runs', icon: List, isVerifyTab: true, verifyTabValue: 'runs' },
        { label: 'Certificates', icon: Award, isVerifyTab: true, verifyTabValue: 'certificates' },
        { label: 'Start Verification', icon: Plus, kind: 'primary', action: 'startVerification' },
      ],
    },
  },
];

function resolveConfig(pathname: string): PageConfig {
  return PAGE_CONFIGS.find((entry) => entry.match(pathname))?.config ?? {
    name: 'Echelon',
    eyebrow: 'Workspace',
    buttons: [],
  };
}

function getActionHandler(action: string, actionsRef: MutableRefObject<TopActionBarActions>): (() => void) | undefined {
  return actionsRef.current[action];
}

function buttonClass(active = false, kind: 'default' | 'primary' | 'pill' = 'default') {
  if (kind === 'pill') {
    return 'rounded-full border border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-2.5 py-1 font-mono text-[11px] font-medium text-[var(--e-text-secondary)]';
  }

  if (kind === 'primary') {
    return clsx(
      'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-[13px] font-semibold transition',
      'border-[var(--e-purple-200)] bg-[var(--e-purple-500)] text-[var(--e-text-inverse)] hover:bg-[var(--e-purple-400)]',
    );
  }

  return clsx(
    'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-[13px] font-medium transition',
    active
      ? 'border-[var(--e-purple-200)] bg-[var(--e-purple-50)] text-[var(--e-purple-700)]'
      : 'border-[var(--e-border-primary)] bg-[var(--e-bg-card)] text-[var(--e-text-secondary)] hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-primary)]',
  );
}

export function TopActionBar({ onHamburgerClick }: TopActionBarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const config = resolveConfig(location.pathname);
  const { actionsRef } = useTopActionBarActions();
  const { activeTab, setActiveTab } = useAgentsUi();
  const { viewMode, setViewMode } = useRlmfUi();
  const { activeTab: verifyTab, setActiveTab: setVerifyTab } = useVerifyUi();

  return (
    <div className="sticky top-14 z-10 border-b border-[var(--e-border-primary)] bg-[var(--e-bg-card)]/90 px-6 py-4 backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onHamburgerClick}
            className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-md text-[var(--e-text-muted)] transition hover:bg-[var(--e-bg-hover)] hover:text-[var(--e-text-secondary)] md:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-4 w-4" />
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {config.buttons.map((btn) => {
            if (btn.isTab) {
              const active = activeTab === btn.tabValue;
              const Icon = btn.icon;
              return (
                <button
                  key={btn.label}
                  type="button"
                  onClick={() => btn.tabValue && setActiveTab(btn.tabValue)}
                  className={buttonClass(active)}
                >
                  {Icon ? <Icon className="h-4 w-4" /> : null}
                  <span>{btn.label}</span>
                </button>
              );
            }

            if (btn.isRlmfViewTab) {
              const active = viewMode === btn.rlmfViewValue;
              const Icon = btn.icon;
              return (
                <button
                  key={btn.label}
                  type="button"
                  onClick={() => btn.rlmfViewValue && setViewMode(btn.rlmfViewValue)}
                  className={buttonClass(active)}
                >
                  {Icon ? <Icon className="h-4 w-4" /> : null}
                  <span>{btn.label}</span>
                </button>
              );
            }

            if (btn.isVerifyTab) {
              const active = verifyTab === btn.verifyTabValue;
              const Icon = btn.icon;
              return (
                <button
                  key={btn.label}
                  type="button"
                  onClick={() => btn.verifyTabValue && setVerifyTab(btn.verifyTabValue)}
                  className={buttonClass(active)}
                >
                  {Icon ? <Icon className="h-4 w-4" /> : null}
                  <span>{btn.label}</span>
                </button>
              );
            }

            if (btn.kind === 'pill') {
              return (
                <span key={btn.label} className={buttonClass(false, 'pill')}>
                  {btn.label}
                </span>
              );
            }

            const Icon = btn.icon;
            return (
              <button
                key={btn.label}
                type="button"
                onClick={() => {
                  if (btn.action === 'createTheatre') {
                    navigate('/theatres/create');
                    return;
                  }

                  const handler = btn.action ? getActionHandler(btn.action, actionsRef) : undefined;
                  if (handler) handler();
                }}
                className={buttonClass(false, btn.kind === 'primary' ? 'primary' : 'default')}
              >
                {Icon ? <Icon className="h-4 w-4" /> : null}
                <span>{btn.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default TopActionBar;
