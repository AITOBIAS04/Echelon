import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { FieldKit } from './components/fieldkit/FieldKit';
import { Blackbox } from './components/blackbox/Blackbox';
import { TimelineDetailPage } from './pages/TimelineDetailPage';
import { HomePage } from './pages/HomePage';
import { LaunchpadPage } from './pages/LaunchpadPage';
import { LaunchpadDetailPage } from './pages/LaunchpadDetailPage';
import { LaunchpadNewPage } from './pages/LaunchpadNewPage';
import { SigintRedirect } from './components/routing/SigintRedirect';
import { AgentRoster } from './components/agents/AgentRoster';
import { AgentDetail } from './components/agents/AgentDetail';
import { ErrorBoundary } from './components/system/ErrorBoundary';
import { VRFPage } from './pages/VRFPage';
import { RLMFPage } from './pages/RLMFPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <ErrorBoundary>
            <HomePage />
          </ErrorBoundary>
        ),
      },
      {
        path: 'sigint',
        element: <SigintRedirect />,
      },
      {
        path: 'fieldkit',
        element: <FieldKit />,
      },
      {
        path: 'blackbox',
        element: <Blackbox />,
      },
      {
        path: 'timeline/:timelineId',
        element: <TimelineDetailPage />,
      },
      {
        path: 'agents',
        element: <AgentRoster />,
      },
      {
        path: 'agent/:agentId',
        element: <AgentDetail />,
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
      {
        path: 'vrf',
        element: (
          <ErrorBoundary>
            <VRFPage />
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
    ],
  },
]);
