import { AlertTriangle, Clock } from 'lucide-react';
import type { Paradox } from '../../types';
import { useState, useEffect } from 'react';

interface ParadoxAlertProps {
  paradox: Paradox;
  onExtract?: () => void;
  onAbandon?: () => void;
}

export function ParadoxAlert({ paradox }: ParadoxAlertProps) {
  const [timeRemaining, setTimeRemaining] = useState(paradox.time_remaining_seconds);
  const [showExtractionModal, setShowExtractionModal] = useState(false);
  const [showAbandonModal, setShowAbandonModal] = useState(false);

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
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => setShowExtractionModal(true)}
          className="px-3 py-1.5 bg-red-900/50 border border-red-500 text-red-400 rounded text-xs hover:bg-red-900 transition-colors flex items-center gap-1"
        >
          🛡️ EXTRACT ({paradox.extraction_cost_echelon} $ECHELON)
        </button>
        <button
          onClick={() => setShowAbandonModal(true)}
          className="px-3 py-1.5 bg-gray-900/50 border border-gray-600 text-gray-400 rounded text-xs hover:bg-gray-800 transition-colors flex items-center gap-1"
        >
          ☠️ ABANDON
        </button>
      </div>

      {/* Extraction Modal */}
      {showExtractionModal && (
        <div 
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
          onClick={() => setShowExtractionModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-cyan-500/50 rounded-lg p-6 max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-cyan-400 font-bold text-lg mb-4">⚠️ EXTRACTION PROTOCOL</h3>
            <p className="text-gray-400 text-sm mb-4">
              Deploying an agent to extract this paradox will cost{' '}
              <span className="text-amber-400 font-bold">
                {paradox.extraction_cost_echelon} $ECHELON
              </span>
              {' '}and risk agent sanity.
            </p>
            <p className="text-yellow-400 text-xs mb-6">
              🔒 Wallet connection required. Feature available in full release.
            </p>
            <div className="flex gap-3">
              <button
                disabled
                className="flex-1 px-4 py-2 bg-cyan-900/30 border border-cyan-500/50 text-cyan-400/50 rounded cursor-not-allowed"
              >
                CONNECT WALLET
              </button>
              <button
                onClick={() => setShowExtractionModal(false)}
                className="px-4 py-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700"
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Abandon Modal */}
      {showAbandonModal && (
        <div 
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
          onClick={() => setShowAbandonModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-red-500/50 rounded-lg p-6 max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-red-400 font-bold text-lg mb-4">☠️ ABANDON TIMELINE</h3>
            <p className="text-gray-400 text-sm mb-4">
              Abandoning this timeline will permanently close all positions and forfeit any active agents.
            </p>
            <p className="text-yellow-400 text-xs mb-6">
              ⚠️ This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                disabled
                className="flex-1 px-4 py-2 bg-red-900/30 border border-red-500/50 text-red-400/50 rounded cursor-not-allowed"
              >
                CONFIRM ABANDON
              </button>
              <button
                onClick={() => setShowAbandonModal(false)}
                className="px-4 py-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700"
              >
                CANCEL
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
