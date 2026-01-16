import { useState, useEffect } from 'react';
import { useBreaches } from '../hooks/useBreaches';
import { BreachList } from '../components/breach/BreachList';
import { BreachDetail } from '../components/breach/BreachDetail';
import { calculateBreachStats } from '../api/mocks/breaches';
import { AlertCircle } from 'lucide-react';

/**
 * BreachConsolePage Component
 * 
 * Main page for the Breach Console, displaying breach list and details
 * in a two-column layout.
 */
export function BreachConsolePage() {
  const { data: breaches = [], isLoading, error, refetch } = useBreaches();
  const [selectedBreachId, setSelectedBreachId] = useState<string | undefined>();

  // Calculate stats
  const stats = calculateBreachStats(breaches);

  // Default selection: first critical breach, or first active breach
  useEffect(() => {
    if (breaches.length > 0 && !selectedBreachId) {
      const criticalBreach = breaches.find((b) => b.severity === 'critical');
      const activeBreach = breaches.find((b) => b.status === 'active');
      const firstBreach = breaches[0];

      setSelectedBreachId(
        criticalBreach?.id || activeBreach?.id || firstBreach.id
      );
    }
  }, [breaches, selectedBreachId]);

  const selectedBreach = breaches.find((b) => b.id === selectedBreachId);

  const handleBreachClick = (breachId: string) => {
    setSelectedBreachId(breachId);
  };

  const handleAction = (actionId: string) => {
    console.log('Execute action:', actionId);
    // TODO: Implement action execution
  };

  const handleResolve = () => {
    console.log('Resolve breach:', selectedBreachId);
    // TODO: Implement breach resolution
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="h-[calc(100vh-4rem)] bg-[#0D0D0D] p-6">
        <div className="max-w-7xl mx-auto h-full flex flex-col">
          {/* Header Skeleton */}
          <div className="mb-6">
            <div className="h-8 bg-gray-800 w-48 rounded mb-4"></div>
            <div className="flex gap-4">
              <div className="h-6 bg-gray-800 w-32 rounded"></div>
              <div className="h-6 bg-gray-800 w-32 rounded"></div>
              <div className="h-6 bg-gray-800 w-32 rounded"></div>
            </div>
          </div>

          {/* Two-column skeleton */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-[40%_1fr] gap-6">
            {/* Left column skeleton */}
            <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] animate-pulse">
              <div className="p-4 space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-24 bg-gray-800 rounded"></div>
                ))}
              </div>
            </div>

            {/* Right column skeleton */}
            <div className="bg-[#111111] rounded-lg border border-[#1A1A1A] animate-pulse">
              <div className="p-4 space-y-4">
                <div className="h-8 bg-gray-800 rounded w-3/4"></div>
                <div className="h-4 bg-gray-800 rounded w-full"></div>
                <div className="h-4 bg-gray-800 rounded w-5/6"></div>
                <div className="h-32 bg-gray-800 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-[calc(100vh-4rem)] bg-[#0D0D0D] p-6 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-terminal-text mb-2">
            Error loading breaches
          </h2>
          <p className="text-sm text-terminal-muted mb-4">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-terminal-panel border border-red-500 rounded text-sm text-red-500 hover:bg-red-500/20 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Count breaches by status
  const activeCount = breaches.filter((b) => b.status === 'active').length;
  const investigatingCount = breaches.filter((b) => b.status === 'investigating').length;
  const resolvedCount = breaches.filter((b) => b.status === 'resolved').length;

  return (
    <div className="h-[calc(100vh-4rem)] bg-[#0D0D0D] p-6 overflow-hidden">
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-terminal-text uppercase mb-4">
            BREACH CONSOLE
          </h1>
          <div className="flex items-center gap-6 flex-wrap">
            {/* Stats Summary */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-terminal-muted">Stats:</span>
              <span className="text-terminal-text font-semibold">
                {activeCount} Active
              </span>
              <span className="text-terminal-muted">|</span>
              <span className="text-terminal-text font-semibold">
                {investigatingCount} Investigating
              </span>
              <span className="text-terminal-muted">|</span>
              <span className="text-terminal-text font-semibold">
                {resolvedCount} Resolved
              </span>
            </div>

            {/* Severity Breakdown */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-terminal-muted uppercase">Severity:</span>
              {(['critical', 'high', 'medium', 'low'] as const).map((severity) => {
                const count = stats.bySeverity[severity];
                if (count === 0) return null;

                const colors = {
                  critical: 'bg-red-500/20 border-red-500 text-red-500',
                  high: 'bg-orange-500/20 border-orange-500 text-orange-500',
                  medium: 'bg-amber-500/20 border-amber-500 text-amber-500',
                  low: 'bg-gray-500/20 border-gray-500 text-gray-500',
                };

                return (
                  <span
                    key={severity}
                    className={`px-2 py-0.5 rounded text-xs font-semibold border capitalize ${colors[severity]}`}
                  >
                    {severity}: {count}
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        {/* Two-column layout */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-[40%_1fr] gap-6 min-h-0">
          {/* Left Column: BreachList */}
          <div className="min-h-0 flex flex-col">
            <BreachList
              breaches={breaches}
              onBreachClick={handleBreachClick}
              selectedBreachId={selectedBreachId}
            />
          </div>

          {/* Right Column: BreachDetail */}
          <div className="min-h-0 flex flex-col">
            {selectedBreach ? (
              <BreachDetail
                breach={selectedBreach}
                onAction={handleAction}
                onResolve={handleResolve}
              />
            ) : (
              <div className="h-full bg-[#111111] rounded-lg border border-[#1A1A1A] p-8 flex flex-col items-center justify-center text-center">
                <AlertCircle className="w-16 h-16 text-terminal-muted mb-4 opacity-50" />
                <h3 className="text-lg font-semibold text-terminal-text mb-2">
                  No breach selected
                </h3>
                <p className="text-sm text-terminal-muted">
                  Select a breach from the list to view details
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
