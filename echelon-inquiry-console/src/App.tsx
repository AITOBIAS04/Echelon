import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { InquiryFlowProvider } from './hooks/useInquiryFlow';
import { Shell } from './components/layout/Shell';
import { SignalFeed } from './components/signal-feed/SignalFeed';
import { InquiryConfig } from './components/inquiry-config/InquiryConfig';

// Placeholder screens — will be replaced in Sprint 3
function PlaceholderScreen({ name }: { name: string }) {
  return (
    <div className="animate-fade-slide-up rounded-lg border border-echelon-border bg-white p-8 shadow-sm">
      <h2 className="text-lg font-semibold text-echelon-navy">{name}</h2>
      <p className="mt-2 text-sm text-slate-500">
        This screen will be implemented in a subsequent sprint.
      </p>
    </div>
  );
}

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
        element: <PlaceholderScreen name="Screen 3: Construct Execution" />,
      },
      {
        path: 'certificate',
        element: <PlaceholderScreen name="Screen 4: Certificate Issued" />,
      },
      {
        path: 'tier-gate',
        element: <PlaceholderScreen name="Screen 5: Tier Gate" />,
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
