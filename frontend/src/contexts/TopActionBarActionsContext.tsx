import { createContext, useContext, useRef, type ReactNode } from 'react';

/**
 * Actions that can be registered by pages for TopActionBar buttons
 */
export interface TopActionBarActions {
  onAlert?: () => void;
  onCompare?: () => void;
  onLive?: () => void;
  onNewTimeline?: () => void;
  onRefresh?: () => void;
  [key: string]: (() => void) | undefined;
}

/**
 * Context for registering TopActionBar button handlers
 * Uses useRef to avoid re-renders when actions are registered
 */
interface TopActionBarActionsContextValue {
  actionsRef: React.MutableRefObject<TopActionBarActions>;
}

const TopActionBarActionsContext = createContext<TopActionBarActionsContextValue | null>(null);

export function useTopActionBarActions() {
  const context = useContext(TopActionBarActionsContext);
  if (!context) {
    throw new Error('useTopActionBarActions must be used within a TopActionBarActionsProvider');
  }
  return context;
}

interface TopActionBarActionsProviderProps {
  children: ReactNode;
}

export function TopActionBarActionsProvider({ children }: TopActionBarActionsProviderProps) {
  const actionsRef = useRef<TopActionBarActions>({});

  return (
    <TopActionBarActionsContext.Provider value={{ actionsRef }}>
      {children}
    </TopActionBarActionsContext.Provider>
  );
}

/**
 * Hook for pages to register their TopActionBar button handlers
 * Uses useRef to avoid triggering re-renders when actions change
 */
export function useRegisterTopActionBarActions(actions: TopActionBarActions) {
  const { actionsRef } = useTopActionBarActions();
  
  // Update the ref with new actions (no re-render)
  // This is safe to call during render since we use a ref
  actionsRef.current = actions;
}
