import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { FieldKit } from './components/fieldkit/FieldKit';
import { Blackbox } from './components/blackbox/Blackbox';
import { TimelineDetailPage } from './pages/TimelineDetailPage';
import { BreachConsolePage } from './pages/BreachConsolePage';
import { HomePage } from './pages/HomePage';
import { LaunchpadPage } from './pages/LaunchpadPage';
import { LaunchpadDetailPage } from './pages/LaunchpadDetailPage';
import { LaunchpadNewPage } from './pages/LaunchpadNewPage';
import { SigintRedirect } from './components/routing/SigintRedirect';
import { AgentRoster } from './components/agents/AgentRoster';
import { AgentDetail } from './components/agents/AgentDetail';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
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
        path: 'breaches',
        element: <BreachConsolePage />,
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

