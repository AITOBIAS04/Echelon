/**
 * VerifyUiContext — shared tab state for Verify page and TopActionBar.
 *
 * Follows the same pattern as AgentsUiContext.
 */

import { createContext, useContext, useState, type ReactNode } from 'react';

export type VerifyTab = 'runs' | 'certificates';

interface VerifyUiContextValue {
  activeTab: VerifyTab;
  setActiveTab: (tab: VerifyTab) => void;
}

const VerifyUiContext = createContext<VerifyUiContextValue | null>(null);

export function useVerifyUi() {
  const context = useContext(VerifyUiContext);
  if (!context) {
    throw new Error('useVerifyUi must be used within a VerifyUiProvider');
  }
  return context;
}

export function VerifyUiProvider({ children }: { children: ReactNode }) {
  const [activeTab, setActiveTab] = useState<VerifyTab>('runs');

  return (
    <VerifyUiContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </VerifyUiContext.Provider>
  );
}
