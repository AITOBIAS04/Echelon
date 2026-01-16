import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { SigintPanel } from './components/sigint/SigintPanel';
import { FieldKit } from './components/fieldkit/FieldKit';
import { Blackbox } from './components/blackbox/Blackbox';
import { TimelineDetail } from './components/timeline/TimelineDetail';
import { AgentRoster } from './components/agents/AgentRoster';
import { AgentDetail } from './components/agents/AgentDetail';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <SigintPanel />,
      },
      {
        path: 'sigint',
        element: <SigintPanel />,
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
        element: <TimelineDetail />,
      },
      {
        path: 'agents',
        element: <AgentRoster />,
      },
      {
        path: 'agent/:agentId',
        element: <AgentDetail />,
      },
    ],
  },
]);

