import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { InquiryFlowProvider } from './hooks/useInquiryFlow';
import { Shell } from './components/layout/Shell';
import { SignalFeed } from './components/signal-feed/SignalFeed';
import { InquiryConfig } from './components/inquiry-config/InquiryConfig';
import { ExecutionView } from './components/execution/ExecutionView';
import { CertificateView } from './components/certificate/CertificateView';
import { TierGate } from './components/tier-gate/TierGate';

const router = createBrowserRouter([
  {
    element: <Shell />,
    children: [
      { index: true, element: <Navigate to="/signal-feed" replace /> },
      {
        path: 'signal-feed',
        element: <SignalFeed />,
      },
      {
        path: 'configure',
        element: <InquiryConfig />,
      },
      {
        path: 'execute',
        element: <ExecutionView />,
      },
      {
        path: 'certificate',
        element: <CertificateView />,
      },
      {
        path: 'tier-gate',
        element: <TierGate />,
      },
    ],
  },
]);

export default function App() {
  return (
    <InquiryFlowProvider>
      <RouterProvider router={router} />
    </InquiryFlowProvider>
  );
}
