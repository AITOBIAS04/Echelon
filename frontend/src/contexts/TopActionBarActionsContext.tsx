import { createContext, useContext, useCallback, useState, type ReactNode } from 'react';

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
 * Pages register their handlers, TopActionBar reads and invokes them
 */
interface TopActionBarActionsContextValue {
  actions: TopActionBarActions;
  setActions: (actions: TopActionBarActions) => void;
  clearActions: () => void;
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
  const [actions, setActions] = useState<TopActionBarActions>({});

  const clearActions = useCallback(() => {
    setActions({});
  }, []);

  return (
    <TopActionBarActionsContext.Provider value={{ actions, setActions, clearActions }}>
      {children}
    </TopActionBarActionsContext.Provider>
  );
}

/**
 * Hook for pages to register their TopActionBar button handlers
 * Should be called in useEffect with empty deps to register on mount, clear on unmount
 */
export function useRegisterTopActionBarActions(actions: TopActionBarActions) {
  const { setActions } = useTopActionBarActions();

  // Register actions on mount
  // Note: We don't clear on unmount to preserve actions during navigation
  // Individual pages can call clearActions() (available via useTopActionBarActions) before unmount if needed
  if (Object.keys(actions).length > 0) {
    setActions(actions);
  }
}
