import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
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
import { VRFPage } from './pages/VRFPage';
import { RLMFPage } from './pages/RLMFPage';
import { BreachConsolePage } from './pages/BreachConsolePage';
import { ExportConsolePage } from './pages/ExportConsolePage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      // Default route → Marketplace
      {
        index: true,
        element: <Navigate to="/marketplace" replace />,
      },
      {
        path: 'marketplace',
        element: (
          <ErrorBoundary>
            <MarketplacePage />
          </ErrorBoundary>
        ),
      },
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
        path: 'agents',
        element: (
          <ErrorBoundary>
            <AgentRoster />
          </ErrorBoundary>
        ),
      },
      {
        path: 'agents/breach',
        element: (
          <ErrorBoundary>
            <BreachConsolePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'agents/export',
        element: (
          <ErrorBoundary>
            <ExportConsolePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'agent/:agentId',
        element: (
          <ErrorBoundary>
            <AgentDetail />
          </ErrorBoundary>
        ),
      },
      {
        path: 'timeline/:timelineId',
        element: (
          <ErrorBoundary>
            <TimelineDetailPage />
          </ErrorBoundary>
        ),
      },
      // Legacy routes — keep accessible but hidden from nav
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
