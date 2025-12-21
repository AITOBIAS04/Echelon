import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import { SigintPanel } from './components/sigint/SigintPanel';
import { ParadoxPanel } from './components/paradox/ParadoxPanel';
import { FieldKitPanel } from './components/fieldkit/FieldKitPanel';
import { BreachesModal } from './components/paradox/BreachesModal';
import { useParadoxes } from './hooks/useParadoxes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

type PanelType = 'sigint' | 'paradox' | 'field-kit';

function AppContent() {
  const [activePanel, setActivePanel] = useState<PanelType>('sigint');
  const [showBreachesModal, setShowBreachesModal] = useState(false);
  const { data: paradoxData } = useParadoxes();
  const paradoxCount = paradoxData?.total_active || 0;
  const paradoxes = paradoxData?.paradoxes || [];

  // Debug: Log which panel is active
  console.log('[App] Active panel:', activePanel);
  console.log('[App] Modal open?', showBreachesModal);
  console.log('[App] Total paradoxes:', paradoxes.length);

  const renderPanel = () => {
    console.log('[App] Rendering panel:', activePanel);
    switch (activePanel) {
      case 'sigint':
        return <SigintPanel />;
      case 'paradox':
        return <ParadoxPanel />;
      case 'field-kit':
        return <FieldKitPanel />;
      default:
        return <SigintPanel />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-terminal-bg">
      <Header 
        paradoxCount={paradoxCount} 
        onBreachesClick={() => setShowBreachesModal(true)}
      />
      <div className="flex-1 flex min-h-0 relative">
        <Sidebar activePanel={activePanel} onPanelChange={setActivePanel} />
        <main className="flex-1 min-h-0 overflow-hidden relative z-0">
          {renderPanel()}
        </main>
      </div>
      
      {/* Breaches Modal */}
      {showBreachesModal && (
        <BreachesModal 
          paradoxes={paradoxes} 
          onClose={() => setShowBreachesModal(false)} 
        />
      )}
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
