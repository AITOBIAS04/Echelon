import { AlertTriangle, Clock, Skull, Zap } from 'lucide-react';
import type { Paradox } from '../../types';
import { useState, useEffect } from 'react';

interface ParadoxAlertProps {
  paradox: Paradox;
  onExtract?: () => void;
  onAbandon?: () => void;
}

export function ParadoxAlert({ paradox, onExtract, onAbandon }: ParadoxAlertProps) {
  const [timeRemaining, setTimeRemaining] = useState(paradox.time_remaining_seconds);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const hours = Math.floor(timeRemaining / 3600);
  const minutes = Math.floor((timeRemaining % 3600) / 60);
  const seconds = timeRemaining % 60;

  const urgency = 
    timeRemaining < 3600 ? 'CRITICAL' :
    timeRemaining < 7200 ? 'HIGH' :
    'ELEVATED';

  const urgencyColor =
    urgency === 'CRITICAL' ? 'border-echelon-red bg-echelon-red/10' :
    urgency === 'HIGH' ? 'border-echelon-amber bg-echelon-amber/10' :
    'border-echelon-purple bg-echelon-purple/10';

  return (
    <div className={`terminal-panel ${urgencyColor} p-4 relative z-0`} style={{ position: 'relative' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-echelon-red animate-pulse" />
          <span className="font-display text-sm text-echelon-red uppercase tracking-wider">
            Containment Breach
          </span>
          <span className="text-xs px-2 py-0.5 bg-echelon-red/20 text-echelon-red rounded">
            {paradox.severity_class.replace('CLASS_', '').replace('_', ' ')}
          </span>
        </div>
        <div className="text-xs text-terminal-muted">
          {paradox.id}
        </div>
      </div>

      {/* Timeline Info */}
      <div className="mb-4">
        <h3 className="text-lg font-medium text-terminal-text">
          {paradox.timeline_name}
        </h3>
        <p className="text-sm text-terminal-muted">
          Logic Gap: {(paradox.logic_gap * 100).toFixed(0)}% | 
          Decay: {paradox.decay_multiplier}x
        </p>
      </div>

      {/* Countdown */}
      <div className="flex items-center justify-center gap-1 mb-4 py-3 bg-terminal-bg rounded">
        <Clock className="w-5 h-5 text-echelon-red mr-2" />
        <span className="font-mono text-3xl text-echelon-red glow-red">
          {String(hours).padStart(2, '0')}:{String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </span>
        <span className="text-xs text-terminal-muted ml-2">until detonation</span>
      </div>

      {/* Extraction Costs */}
      <div className="grid grid-cols-3 gap-3 mb-4 text-center">
        <div className="p-2 bg-terminal-bg rounded">
          <div className="text-xs text-terminal-muted mb-1">USDC Cost</div>
          <div className="text-sm font-mono text-echelon-green">
            ${paradox.extraction_cost_usdc.toFixed(0)}
          </div>
        </div>
        <div className="p-2 bg-terminal-bg rounded">
          <div className="text-xs text-terminal-muted mb-1">$ECHELON</div>
          <div className="text-sm font-mono text-echelon-purple">
            {paradox.extraction_cost_echelon}
          </div>
        </div>
        <div className="p-2 bg-terminal-bg rounded">
          <div className="text-xs text-terminal-muted mb-1">Sanity Cost</div>
          <div className="text-sm font-mono text-echelon-amber">
            {paradox.carrier_sanity_cost}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onExtract}
          className="flex-1 flex items-center justify-center gap-2 py-2 bg-echelon-purple/20 border border-echelon-purple text-echelon-purple rounded hover:bg-echelon-purple/30 transition"
        >
          <Zap className="w-4 h-4" />
          Extract Paradox
        </button>
        <button
          onClick={onAbandon}
          className="flex-1 flex items-center justify-center gap-2 py-2 bg-terminal-bg border border-terminal-border text-terminal-muted rounded hover:border-echelon-red hover:text-echelon-red transition"
        >
          <Skull className="w-4 h-4" />
          Abandon Timeline
        </button>
      </div>
    </div>
  );
}
