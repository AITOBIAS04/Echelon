import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from './components/layout/Header';
import { SigintPanel } from './components/sigint/SigintPanel';
import { useParadoxes } from './hooks/useParadoxes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;

  return (
    <div className="h-screen flex flex-col bg-terminal-bg">
      <Header paradoxCount={paradoxCount} />
      <main className="flex-1 min-h-0">
        <SigintPanel />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
