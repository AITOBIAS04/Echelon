import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInquiryFlow } from '../../hooks/useInquiryFlow';
import { SIGNALS } from '../../data/signals';
import type { Signal } from '../../types/signal';
import { SignalCard } from './SignalCard';
import { SourceBadge } from './SourceBadge';
import { relativeTime, formatPercentage } from '../../utils/format';

export function SignalFeed() {
  const [, dispatch] = useInquiryFlow();
  const navigate = useNavigate();
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);

  function handleCreateInquiry() {
    if (!selectedSignal) return;
    dispatch({ type: 'SELECT_SIGNAL', payload: selectedSignal });
    navigate('/configure');
  }

  return (
    <div className="animate-fade-slide-up">
      <h2 className="mb-1 text-lg font-semibold text-echelon-navy">
        Signal Feed
      </h2>
      <p className="mb-6 text-sm text-slate-500">
        Select a signal to begin a bounded inquiry
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-5">
        {/* Signal list — 60% */}
        <div className="flex flex-col gap-3 md:col-span-3">
          {SIGNALS.map((signal, idx) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              isSelected={selectedSignal?.id === signal.id}
              animationDelay={idx * 200}
              onClick={() => setSelectedSignal(signal)}
            />
          ))}
        </div>

        {/* Detail panel — 40% */}
        <div className="md:col-span-2">
          {selectedSignal ? (
            <div className="sticky top-4 animate-fade-slide-up rounded-lg border border-echelon-border bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-echelon-navy">
                  Signal Detail
                </h3>
                <SourceBadge jurisdiction={selectedSignal.jurisdiction} />
              </div>

              <div className="mt-4 space-y-3">
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-500">
                    Source
                  </span>
                  <p className="text-sm font-medium text-slate-800">
                    {selectedSignal.source_name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {selectedSignal.source_group}
                  </p>
                </div>

                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-500">
                    Headline
                  </span>
                  <p className="text-sm text-slate-800">
                    {selectedSignal.headline}
                  </p>
                </div>

                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-500">
                    Summary
                  </span>
                  <p className="text-sm leading-relaxed text-slate-600">
                    {selectedSignal.summary}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">
                      Confidence
                    </span>
                    <p className="font-mono text-sm text-echelon-data-text">
                      {formatPercentage(selectedSignal.confidence)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">
                      Settlement
                    </span>
                    <p className="text-sm">
                      <span
                        className={`inline-block h-2 w-2 rounded-full ${
                          selectedSignal.settlement_eligible
                            ? 'bg-echelon-success'
                            : 'bg-slate-300'
                        }`}
                      />{' '}
                      <span className="text-slate-700">
                        {selectedSignal.settlement_eligible
                          ? 'Eligible'
                          : 'Not eligible'}
                      </span>
                    </p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">
                      Access
                    </span>
                    <p className="font-mono text-xs text-echelon-data-text">
                      {selectedSignal.access_surface}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-500">
                      Receipt
                    </span>
                    <p className="font-mono text-xs text-echelon-data-text">
                      {selectedSignal.receipt_mode}
                    </p>
                  </div>
                </div>

                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-500">
                    Suggested Class
                  </span>
                  <p className="text-sm font-semibold uppercase tracking-wider text-echelon-navy">
                    {selectedSignal.suggested_class}
                  </p>
                </div>

                <div className="text-right text-xs text-slate-400">
                  {relativeTime(selectedSignal.timestamp)}
                </div>
              </div>

              <button
                onClick={handleCreateInquiry}
                className="mt-6 w-full rounded-md bg-echelon-navy px-6 py-2.5 font-medium text-white transition-colors hover:bg-opacity-90"
              >
                Create Inquiry
              </button>
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-echelon-border">
              <p className="text-sm text-slate-400">
                Select a signal to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
