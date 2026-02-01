import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

export type RlmfViewMode = 'market' | 'robotics';

interface RlmfUiContextType {
  viewMode: RlmfViewMode;
  setViewMode: (mode: RlmfViewMode) => void;
}

const RlmfUiContext = createContext<RlmfUiContextType | undefined>(undefined);

export function RlmfUiProvider({ children }: { children: ReactNode }) {
  const [viewMode, setViewMode] = useState<RlmfViewMode>('market');

  return (
    <RlmfUiContext.Provider value={{ viewMode, setViewMode }}>
      {children}
    </RlmfUiContext.Provider>
  );
}

export function useRlmfUi() {
  const context = useContext(RlmfUiContext);
  if (!context) {
    throw new Error('useRlmfUi must be used within a RlmfUiProvider');
  }
  return context;
}
