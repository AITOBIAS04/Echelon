import { createContext, useContext, useState, type ReactNode } from 'react';

export type AgentsTab = 'roster' | 'intel';

interface AgentsUiContextValue {
  activeTab: AgentsTab;
  setActiveTab: (tab: AgentsTab) => void;
}

const AgentsUiContext = createContext<AgentsUiContextValue | null>(null);

export function useAgentsUi() {
  const context = useContext(AgentsUiContext);
  if (!context) {
    throw new Error('useAgentsUi must be used within an AgentsUiProvider');
  }
  return context;
}

interface AgentsUiProviderProps {
  children: ReactNode;
}

export function AgentsUiProvider({ children }: AgentsUiProviderProps) {
  const [activeTab, setActiveTab] = useState<AgentsTab>('roster');

  return (
    <AgentsUiContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </AgentsUiContext.Provider>
  );
}
