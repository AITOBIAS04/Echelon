/**
 * SignalFeedPanel — Aggregated signal feed across all investigations.
 * Source-badged signal cards with click-through to create investigation.
 */

import { useNavigate } from 'react-router-dom';
import { useInvestigationList, useInvestigationDetail } from '../../hooks/useInvestigation';
import { SignalCard } from './SignalCard';
import type { CounterSignal } from '../../types/investigation';
import { useState, useMemo } from 'react';

export function SignalFeedPanel() {
  const navigate = useNavigate();
  const { investigations, isLoading: listLoading } = useInvestigationList();
  const [selectedInvId, setSelectedInvId] = useState<string | null>(null);

  // Auto-select first investigation with signals if none selected
  const activeInvId = selectedInvId ?? (investigations.length > 0 ? investigations[0].id : null);
  const { investigation, isLoading: detailLoading } = useInvestigationDetail(activeInvId);

  const signals = useMemo(() => {
    if (!investigation) return [];
    return [...investigation.counter_signals.signals].sort(
      (a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime(),
    );
  }, [investigation]);

  const handleCreateFromSignal = (signal: CounterSignal) => {
    const params = new URLSearchParams();
    params.set('signal_class', signal.signal_class);
    if (signal.evidence_ref) {
      params.set('evidence_ref', signal.evidence_ref);
    }
    if (activeInvId) {
      params.set('source_investigation', activeInvId);
    }
    navigate(`/investigation/create?${params.toString()}`);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          Signal Feed
        </h2>
        <p className="text-xs text-terminal-text-muted mt-1">
          Counter-signals detected across investigations. Click to create a follow-up investigation.
        </p>
      </div>

      {/* Investigation filter */}
      {investigations.length > 1 && (
        <div className="flex gap-1 flex-wrap">
          {investigations.map((inv) => (
            <button
              key={inv.id}
              onClick={() => setSelectedInvId(inv.id)}
              className={`px-2 py-1 rounded text-[10px] font-mono transition-colors ${
                activeInvId === inv.id
                  ? 'bg-echelon-cyan/10 text-echelon-cyan border border-echelon-cyan/30'
                  : 'text-terminal-text-muted border border-terminal-border hover:text-terminal-text'
              }`}
            >
              {inv.id}
              {inv.counter_signal_count > 0 && (
                <span className="ml-1 text-[9px]">({inv.counter_signal_count})</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Signal list */}
      {listLoading || detailLoading ? (
        <div className="text-xs text-terminal-text-muted text-center py-8">
          Loading signals...
        </div>
      ) : signals.length === 0 ? (
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-8 text-center">
          <div className="text-xs text-terminal-text-muted">
            No counter-signals detected yet.
          </div>
          <div className="text-[10px] text-terminal-text-muted mt-1">
            Signals appear as investigations process evidence and detect contradictions.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {signals.map((signal) => (
            <SignalCard
              key={signal.counter_signal_id}
              signal={signal}
              onCreateInvestigation={handleCreateFromSignal}
            />
          ))}
        </div>
      )}
    </div>
  );
}
