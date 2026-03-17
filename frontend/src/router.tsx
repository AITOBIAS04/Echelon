import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { PublicShell } from './components/public/PublicShell';

/** Redirect that preserves :agentId param from old /agent/:agentId to /fleet/:agentId */
function AgentRedirect() {
  const { agentId } = useParams();
  return <Navigate to={`/fleet/${agentId}`} replace />;
}
function LaunchpadRedirect() {
  return <Navigate to="/scenario-packs" replace />;
}

function LaunchpadNewRedirect() {
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode');

  if (mode === 'theatre') {
    return <Navigate to="/theatres/create" replace />;
  }

  if (mode === 'incident' || mode === 'osint') {
    return <Navigate to="/investigation/create" replace />;
  }

  return <Navigate to="/theatres/create" replace />;
}
import { PortfolioPage } from './pages/PortfolioPage';
import { TimelineDetailPage } from './pages/TimelineDetailPage';
import { MarketplacePage } from './pages/MarketplacePage';
import { BlackboxPage } from './pages/BlackboxPage';
import { AgentRoster } from './components/agents/AgentRoster';
import { AgentDetail } from './components/agents/AgentDetail';
import { ErrorBoundary } from './components/system/ErrorBoundary';
import { RouteErrorBoundary } from './components/common/RouteErrorBoundary';
import { VRFPage } from './pages/VRFPage';
import { RLMFPage } from './pages/RLMFPage';
import { BreachConsolePage } from './pages/BreachConsolePage';
// ExportConsolePage — now redirected to /rlmf
// InvestigationPage — now redirected to /workspace
import { HomePage } from './pages/HomePage';
// SignalFeedPage — now redirected to /workspace
import { CreateInvestigationPage } from './pages/CreateInvestigationPage';
import { ConvergencePage } from './pages/ConvergencePage';

// ── New pages (Cycle 017 integration) ─────────────────────────────────
// WorldMonitorPage, WorldMonitorLivePage, SignalMapPage — now redirected to /workspace
import { InvestigationWorkspacePage } from './pages/InvestigationWorkspacePage';
import { CertificatesPage } from './pages/CertificatesPage';
import { CreateTheatrePage } from './pages/CreateTheatrePage';
import { ScenarioPacksPage } from './pages/ScenarioPacksPage';
import { ScenarioPackDetailPage } from './pages/ScenarioPackDetailPage';
import { AgentMatrixPage } from './pages/AgentMatrixPage';

/**
 * Retry dynamic import once with a full page reload on failure.
 * Handles stale chunk hashes after Vercel/Pages redeployment.
 */
function lazyWithRetry(importFn: () => Promise<{ default: React.ComponentType }>) {
  return lazy(() =>
    importFn().catch(() => {
      // Chunk hash mismatch after deploy — reload once
      const key = 'chunk-retry';
      if (!sessionStorage.getItem(key)) {
        sessionStorage.setItem(key, '1');
        window.location.reload();
      }
      // Fallback: rethrow so error boundary catches it
      return importFn();
    }),
  );
}

const VerifyPage = lazyWithRetry(() =>
  import('./pages/VerifyPage').then((m) => ({ default: m.VerifyPage }))
);

// ── Public pages (unauthenticated) ──────────────────────────────────────
const PublicLandingPage = lazyWithRetry(() => import('./pages/PublicLandingPage'));
const PublicResultsPage = lazyWithRetry(() => import('./pages/PublicResultsPage'));
const PublicVerifyPage = lazyWithRetry(() => import('./pages/PublicVerifyPage'));

export const router = createBrowserRouter([
  // Legacy: /public/* redirects to new root paths
  { path: '/public', element: <Navigate to="/" replace /> },
  { path: '/public/results', element: <Navigate to="/results" replace /> },
  { path: '/public/verify', element: <Navigate to="/verify-public" replace /> },
  { path: '/public/certificates', element: <Navigate to="/results" replace /> },

  // ── All pages (AppLayout — sidebar + header) ──────────────────────────
  {
    element: <AppLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      // ── Echelon (public pages inside operator shell) ────────────────
      {
        path: '/',
        element: <PublicShell><PublicLandingPage /></PublicShell>,
      },
      {
        path: '/results',
        element: <PublicShell><PublicResultsPage /></PublicShell>,
      },
      {
        path: '/results/:resultId',
        element: <PublicShell><PublicResultsPage /></PublicShell>,
      },
      {
        path: '/verify-public',
        element: <PublicShell><PublicVerifyPage /></PublicShell>,
      },

      // ── Mission Control ────────────────────────────────────────────
      {
        path: '/home',
        element: (
          <ErrorBoundary>
            <HomePage />
          </ErrorBoundary>
        ),
      },

      // ── Theatres (renamed from marketplace) ─────────────────────────
      {
        path: '/theatres',
        element: (
          <ErrorBoundary>
            <MarketplacePage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/theatres/create',
        element: (
          <ErrorBoundary>
            <CreateTheatrePage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/theatre/:theatreId',
        element: (
          <ErrorBoundary>
            <TimelineDetailPage />
          </ErrorBoundary>
        ),
      },
      // Keep /marketplace as redirect for backward compat
      {
        path: '/marketplace',
        element: <Navigate to="/theatres" replace />,
      },

      // ── Fleet (renamed from agents) ─────────────────────────────────
      {
        path: '/fleet',
        element: (
          <ErrorBoundary>
            <AgentRoster />
          </ErrorBoundary>
        ),
      },
      {
        path: '/fleet/:agentId',
        element: (
          <ErrorBoundary>
            <AgentDetail />
          </ErrorBoundary>
        ),
      },
      // Keep /agents as redirect
      {
        path: '/agents',
        element: <Navigate to="/fleet" replace />,
      },
      {
        path: '/agent/:agentId',
        element: <AgentRedirect />,
      },

      // ── Agent Matrix (Fleet sub-route) ──────────────────────────────
      {
        path: '/fleet/matrix',
        element: (
          <ErrorBoundary>
            <AgentMatrixPage />
          </ErrorBoundary>
        ),
      },
      // Legacy redirect: /matrix → /fleet/matrix
      {
        path: '/matrix',
        element: <Navigate to="/fleet/matrix" replace />,
      },

      // ── Paradox Console (renamed from agents/breach) ────────────────
      {
        path: '/paradox-console',
        element: (
          <ErrorBoundary>
            <BreachConsolePage />
          </ErrorBoundary>
        ),
      },
      // Keep old route as redirect
      {
        path: '/agents/breach',
        element: <Navigate to="/paradox-console" replace />,
      },

      // ── Investigation Workspace (replaces world-monitor, signal-map, investigation)
      {
        path: '/workspace',
        element: (
          <ErrorBoundary>
            <InvestigationWorkspacePage />
          </ErrorBoundary>
        ),
      },
      // Legacy routes → workspace redirects
      {
        path: '/world-monitor',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/world-monitor/live',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/signal-map',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/certificates',
        element: (
          <ErrorBoundary>
            <CertificatesPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/scenario-packs',
        element: (
          <ErrorBoundary>
            <ScenarioPacksPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/scenario-packs/:templateId',
        element: (
          <ErrorBoundary>
            <ScenarioPackDetailPage />
          </ErrorBoundary>
        ),
      },

      // ── Kept as-is ──────────────────────────────────────────────────
      {
        path: '/analytics',
        element: (
          <ErrorBoundary>
            <BlackboxPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/portfolio',
        element: (
          <ErrorBoundary>
            <PortfolioPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/rlmf',
        element: (
          <ErrorBoundary>
            <RLMFPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/vrf',
        element: (
          <ErrorBoundary>
            <VRFPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/investigation',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/investigation/signals',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/investigation/create',
        element: (
          <ErrorBoundary>
            <CreateInvestigationPage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/convergence',
        element: (
          <ErrorBoundary>
            <ConvergencePage />
          </ErrorBoundary>
        ),
      },
      {
        path: '/verify',
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
        path: '/agents/export',
        element: <Navigate to="/rlmf" replace />,
      },

      // ── Timeline detail (backward compat — also served at /theatre/:id) ──
      {
        path: '/timeline/:timelineId',
        element: (
          <ErrorBoundary>
            <TimelineDetailPage />
          </ErrorBoundary>
        ),
      },

      // ── Legacy redirects ────────────────────────────────────────────
      {
        path: '/fieldkit',
        element: <Navigate to="/portfolio" replace />,
      },
      {
        path: '/blackbox',
        element: <Navigate to="/analytics" replace />,
      },
      {
        path: '/launchpad',
        element: <LaunchpadRedirect />,
      },
      {
        path: '/launchpad/:id',
        element: <LaunchpadRedirect />,
      },
      {
        path: '/launchpad/new',
        element: <LaunchpadNewRedirect />,
      },
    ],
  },
]);
