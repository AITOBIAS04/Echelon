import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, useParams } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';

/** Redirect that preserves :agentId param from old /agent/:agentId to /fleet/:agentId */
function AgentRedirect() {
  const { agentId } = useParams();
  return <Navigate to={`/fleet/${agentId}`} replace />;
}
import { PortfolioPage } from './pages/PortfolioPage';
import { TimelineDetailPage } from './pages/TimelineDetailPage';
import { MarketplacePage } from './pages/MarketplacePage';
import { BlackboxPage } from './pages/BlackboxPage';
import { LaunchpadPage } from './pages/LaunchpadPage';
import { LaunchpadDetailPage } from './pages/LaunchpadDetailPage';
import { LaunchpadNewPage } from './pages/LaunchpadNewPage';
import { AgentRoster } from './components/agents/AgentRoster';
import { AgentDetail } from './components/agents/AgentDetail';
import { ErrorBoundary } from './components/system/ErrorBoundary';
import { RouteErrorBoundary } from './components/common/RouteErrorBoundary';
import { VRFPage } from './pages/VRFPage';
import { RLMFPage } from './pages/RLMFPage';
import { BreachConsolePage } from './pages/BreachConsolePage';
// ExportConsolePage — now redirected to /rlmf
import { InvestigationPage } from './pages/InvestigationPage';
import { HomePage } from './pages/HomePage';
// SignalFeedPage — now redirected to /signal-map
import { CreateInvestigationPage } from './pages/CreateInvestigationPage';
import { ConvergencePage } from './pages/ConvergencePage';

// ── New pages (Cycle 017 integration) ─────────────────────────────────
import { WorldMonitorPage } from './pages/WorldMonitorPage';
import { SignalMapPage } from './pages/SignalMapPage';
import { CertificatesPage } from './pages/CertificatesPage';
import { CreateTheatrePage } from './pages/CreateTheatrePage';
import { ScenarioPacksPage } from './pages/ScenarioPacksPage';
import { ScenarioPackDetailPage } from './pages/ScenarioPackDetailPage';

const VerifyPage = lazy(() =>
  import('./pages/VerifyPage').then((m) => ({ default: m.VerifyPage }))
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      // Default route → Dashboard
      {
        index: true,
        element: <Navigate to="/home" replace />,
      },
      {
        path: 'home',
        element: (
          <ErrorBoundary>
            <HomePage />
          </ErrorBoundary>
        ),
      },

      // ── Theatres (renamed from marketplace) ─────────────────────────
      {
        path: 'theatres',
        element: (
          <ErrorBoundary>
            <MarketplacePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'theatres/create',
        element: (
          <ErrorBoundary>
            <CreateTheatrePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'theatre/:theatreId',
        element: (
          <ErrorBoundary>
            <TimelineDetailPage />
          </ErrorBoundary>
        ),
      },
      // Keep /marketplace as redirect for backward compat
      {
        path: 'marketplace',
        element: <Navigate to="/theatres" replace />,
      },

      // ── Fleet (renamed from agents) ─────────────────────────────────
      {
        path: 'fleet',
        element: (
          <ErrorBoundary>
            <AgentRoster />
          </ErrorBoundary>
        ),
      },
      {
        path: 'fleet/:agentId',
        element: (
          <ErrorBoundary>
            <AgentDetail />
          </ErrorBoundary>
        ),
      },
      // Keep /agents as redirect
      {
        path: 'agents',
        element: <Navigate to="/fleet" replace />,
      },
      {
        path: 'agent/:agentId',
        element: <AgentRedirect />,
      },

      // ── Paradox Console (renamed from agents/breach) ────────────────
      {
        path: 'paradox-console',
        element: (
          <ErrorBoundary>
            <BreachConsolePage />
          </ErrorBoundary>
        ),
      },
      // Keep old route as redirect
      {
        path: 'agents/breach',
        element: <Navigate to="/paradox-console" replace />,
      },

      // ── New pages ───────────────────────────────────────────────────
      {
        path: 'world-monitor',
        element: (
          <ErrorBoundary>
            <WorldMonitorPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'signal-map',
        element: (
          <ErrorBoundary>
            <SignalMapPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'certificates',
        element: (
          <ErrorBoundary>
            <CertificatesPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'scenario-packs',
        element: (
          <ErrorBoundary>
            <ScenarioPacksPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'scenario-packs/:templateId',
        element: (
          <ErrorBoundary>
            <ScenarioPackDetailPage />
          </ErrorBoundary>
        ),
      },

      // ── Kept as-is ──────────────────────────────────────────────────
      {
        path: 'analytics',
        element: (
          <ErrorBoundary>
            <BlackboxPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'portfolio',
        element: (
          <ErrorBoundary>
            <PortfolioPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'rlmf',
        element: (
          <ErrorBoundary>
            <RLMFPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'vrf',
        element: (
          <ErrorBoundary>
            <VRFPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'investigation',
        element: (
          <ErrorBoundary>
            <InvestigationPage />
          </ErrorBoundary>
        ),
      },
      // Legacy: /investigation/signals → /signal-map (promoted to top-level)
      {
        path: 'investigation/signals',
        element: <Navigate to="/signal-map" replace />,
      },
      {
        path: 'investigation/create',
        element: (
          <ErrorBoundary>
            <CreateInvestigationPage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'convergence',
        element: (
          <ErrorBoundary>
            <ConvergencePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'verify',
        element: (
          <ErrorBoundary>
            <Suspense
              fallback={
                <div className="p-6 text-terminal-text-muted text-xs">
                  Loading...
                </div>
              }
            >
              <VerifyPage />
            </Suspense>
          </ErrorBoundary>
        ),
      },
      // Legacy: /agents/export → /rlmf (export surface lives under RLMF now)
      {
        path: 'agents/export',
        element: <Navigate to="/rlmf" replace />,
      },

      // ── Timeline detail (backward compat — also served at /theatre/:id) ──
      {
        path: 'timeline/:timelineId',
        element: (
          <ErrorBoundary>
            <TimelineDetailPage />
          </ErrorBoundary>
        ),
      },

      // ── Legacy redirects ────────────────────────────────────────────
      {
        path: 'fieldkit',
        element: <Navigate to="/portfolio" replace />,
      },
      {
        path: 'blackbox',
        element: <Navigate to="/analytics" replace />,
      },
      {
        path: 'launchpad',
        element: <LaunchpadPage />,
      },
      {
        path: 'launchpad/:id',
        element: <LaunchpadDetailPage />,
      },
      {
        path: 'launchpad/new',
        element: <LaunchpadNewPage />,
      },
    ],
  },
]);
