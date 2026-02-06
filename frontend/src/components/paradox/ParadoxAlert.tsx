import { AlertTriangle, Clock, Shield, Skull, X } from 'lucide-react';
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
  const [isExpanded, setIsExpanded] = useState(false);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (showExtractionModal || showAbandonModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showExtractionModal, showAbandonModal]);

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
    <div className={`terminal-panel ${urgencyColor} p-3 sm:p-4`}>
      {/* Header (compact by default) */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-echelon-red animate-pulse flex-shrink-0" />
            <span className="font-display text-sm text-echelon-red uppercase tracking-wider whitespace-nowrap">
              Containment Breach
            </span>
            <span className="text-[10px] px-2 py-0.5 bg-echelon-red/20 text-echelon-red rounded whitespace-nowrap">
              {paradox.severity_class.replace('CLASS_', '').replace('_', ' ')}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <h3 className="text-base sm:text-lg font-medium text-terminal-text truncate">
              {paradox.timeline_name}
            </h3>
            <span className="text-xs text-terminal-text-muted whitespace-nowrap">
              Gap {((paradox.logic_gap || 0) * 100).toFixed(0)}% • {paradox.decay_multiplier}x
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <div className="text-[10px] sm:text-xs text-terminal-text-muted max-w-[140px] sm:max-w-[220px] truncate">
            {paradox.id}
          </div>
          <button
            onClick={() => setIsExpanded((v) => !v)}
            className="text-[10px] px-2 py-1 rounded bg-terminal-bg border border-terminal-border text-terminal-text-muted hover:text-terminal-text hover:border-gray-600 transition-colors whitespace-nowrap"
          >
            {isExpanded ? 'HIDE DETAILS' : 'DETAILS'}
          </button>
        </div>
      </div>

      {/* Compact banner content */}
      {!isExpanded && (
        <div className="mt-3">
          <div className="flex items-center justify-between gap-3 bg-terminal-bg rounded px-3 py-2">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-echelon-red" />
              <span className="font-mono text-xl sm:text-2xl text-echelon-red glow-red">
                {String(hours).padStart(2, '0')}:{String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </span>
              <span className="text-[10px] text-terminal-text-muted hidden sm:inline">until detonation</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] sm:text-xs">
              <span className="text-echelon-green font-mono whitespace-nowrap">
                ${paradox.extraction_cost_usdc.toFixed(0)}
              </span>
              <span className="text-echelon-purple font-mono whitespace-nowrap">
                {paradox.extraction_cost_echelon} ECH
              </span>
              <span className="text-echelon-amber font-mono whitespace-nowrap">
                {paradox.carrier_sanity_cost} SAN
              </span>
            </div>
          </div>

          <div className="flex gap-2 mt-3">
            <button 
              onClick={() => setShowExtractionModal(true)}
              className="flex-1 px-3 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded text-sm font-bold hover:bg-echelon-cyan/30 transition-all flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              EXTRACT
            </button>
            <button 
              onClick={() => setShowAbandonModal(true)}
              className="px-3 py-2 bg-echelon-red/20 border border-echelon-red/50 text-echelon-red rounded text-sm font-bold hover:bg-echelon-red/30 transition-all flex items-center justify-center gap-2"
            >
              <Skull className="w-4 h-4" />
              ABANDON
            </button>
          </div>
        </div>
      )}

      {/* Expanded content (old detailed view, slightly tighter) */}
      {isExpanded && (
        <>
          {/* Countdown */}
          <div className="flex items-center justify-center gap-1 mt-3 mb-3 py-2 bg-terminal-bg rounded">
            <Clock className="w-5 h-5 text-echelon-red mr-2" />
            <span className="font-mono text-2xl sm:text-3xl text-echelon-red glow-red">
              {String(hours).padStart(2, '0')}:{String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </span>
            <span className="text-xs text-terminal-text-muted ml-2">until detonation</span>
          </div>

          {/* Extraction Costs */}
          <div className="grid grid-cols-3 gap-3 mb-3 text-center">
            <div className="p-2 bg-terminal-bg rounded">
              <div className="text-xs text-terminal-text-muted mb-1">USDC Cost</div>
              <div className="text-sm font-mono text-echelon-green">
                ${paradox.extraction_cost_usdc.toFixed(0)}
              </div>
            </div>
            <div className="p-2 bg-terminal-bg rounded">
              <div className="text-xs text-terminal-text-muted mb-1">$ECHELON</div>
              <div className="text-sm font-mono text-echelon-purple">
                {paradox.extraction_cost_echelon}
              </div>
            </div>
            <div className="p-2 bg-terminal-bg rounded">
              <div className="text-xs text-terminal-text-muted mb-1">Sanity Cost</div>
              <div className="text-sm font-mono text-echelon-amber">
                {paradox.carrier_sanity_cost}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 mt-2">
            <button 
              onClick={() => setShowExtractionModal(true)}
              className="flex-1 px-3 py-2.5 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded text-sm font-bold hover:bg-echelon-cyan/30 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              EXTRACT
            </button>
            <button 
              onClick={() => setShowAbandonModal(true)}
              className="px-3 py-2.5 bg-echelon-red/20 border border-echelon-red/50 text-echelon-red rounded text-sm font-bold hover:bg-echelon-red/30 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
            >
              <Skull className="w-4 h-4" />
              ABANDON
            </button>
          </div>
        </>
      )}

      {/* Extraction Modal */}
      {showExtractionModal && (
        <>
          {/* Dark overlay - blocks all background content and pointer events */}
          <div 
            className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990]"
            style={{ pointerEvents: 'auto' }}
            onClick={() => setShowExtractionModal(false)}
          />
          
          {/* Modal content - above overlay */}
          <div 
            className="fixed inset-0 z-[9995] flex items-center justify-center p-4 pointer-events-none"
            onClick={(e) => {
              // Close on backdrop click
              if (e.target === e.currentTarget) setShowExtractionModal(false);
            }}
          >
            <div 
              className="relative bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-4 sm:p-6 max-w-md w-full mx-2 sm:mx-4 animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
            <button 
              onClick={() => setShowExtractionModal(false)}
              className="absolute top-4 right-4 text-terminal-text-muted hover:text-terminal-text transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-echelon-cyan/20 rounded-full flex items-center justify-center border border-echelon-cyan/30">
                <Shield className="w-6 h-6 text-echelon-cyan" />
              </div>
              <div>
                <h3 className="text-echelon-cyan font-bold text-lg">EXTRACTION PROTOCOL</h3>
                <p className="text-terminal-text-muted text-xs">Deploy agent to contain paradox breach</p>
              </div>
            </div>
            
            <div className="bg-echelon-red/20 border border-echelon-red/30 rounded p-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-echelon-red font-bold text-sm">
                  {paradox.severity_class || 'CLASS_2_SEVERE'}
                </span>
                <span className="text-terminal-text-muted text-xs">
                  Logic Gap: {((paradox.logic_gap || 0.45) * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-terminal-text text-sm mt-2">
                Timeline: <span className="text-terminal-text font-bold">{paradox.timeline_name || 'Unknown'}</span>
              </p>
            </div>
            
            <div className="space-y-2 mb-4 bg-terminal-bg/50 rounded p-3">
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">Extraction Cost</span>
                <span className="text-echelon-amber font-bold">500 $ECHELON</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">Agent Sanity Cost</span>
                <span className="text-echelon-purple">-15 Sanity</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">Success Probability</span>
                <span className="text-echelon-green">72%</span>
              </div>
              <div className="border-t border-terminal-border pt-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-terminal-text-muted">Success Reward</span>
                  <span className="text-echelon-cyan font-bold">+250 $ECHELON + Rep</span>
                </div>
              </div>
            </div>
            
            <div className="bg-echelon-amber/20 border border-echelon-amber/30 rounded p-3 mb-6">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-echelon-amber mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-echelon-amber text-sm font-bold">Wallet Connection Required</p>
                  <p className="text-terminal-text-muted text-xs mt-1">
                    Connect wallet and hold $ECHELON to execute extractions. Available Q1 2025.
                  </p>
                </div>
              </div>
            </div>
            
            <button 
              disabled
              className="w-full px-4 py-3 bg-echelon-cyan/20 border border-echelon-cyan/30 text-echelon-cyan/50 rounded font-bold cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              CONNECT WALLET TO EXTRACT
            </button>
            
            <p className="text-center text-terminal-text-muted text-xs mt-4">
              Join waitlist at <span className="text-echelon-cyan">playechelon.io</span>
            </p>
            </div>
          </div>
        </>
      )}

      {/* Abandon Modal */}
      {showAbandonModal && (
        <>
          {/* Dark overlay - blocks all background content and pointer events */}
          <div 
            className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990]"
            style={{ pointerEvents: 'auto' }}
            onClick={() => setShowAbandonModal(false)}
          />
          
          {/* Modal content - above overlay */}
          <div 
            className="fixed inset-0 z-[9995] flex items-center justify-center p-4 pointer-events-none"
            onClick={(e) => {
              // Close on backdrop click
              if (e.target === e.currentTarget) setShowAbandonModal(false);
            }}
          >
            <div 
              className="relative bg-[#0D0D0D] border border-echelon-red/50 rounded-lg p-4 sm:p-6 max-w-md w-full mx-2 sm:mx-4 animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
            <button 
              onClick={() => setShowAbandonModal(false)}
              className="absolute top-4 right-4 text-terminal-text-muted hover:text-terminal-text transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-echelon-red/20 rounded-full flex items-center justify-center border border-echelon-red/30">
                <Skull className="w-6 h-6 text-echelon-red" />
              </div>
              <div>
                <h3 className="text-echelon-red font-bold text-lg">ABANDON TIMELINE</h3>
                <p className="text-terminal-text-muted text-xs">Allow paradox detonation</p>
              </div>
            </div>
            
            <div className="bg-echelon-red/30 border border-echelon-red/50 rounded p-4 mb-4">
              <p className="text-echelon-red text-sm font-bold mb-3">⚠️ CATASTROPHIC CONSEQUENCES</p>
              <ul className="text-terminal-text text-sm space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-echelon-red">•</span>
                  <span>All shards in timeline will be <span className="text-echelon-red font-bold">BURNED</span></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-echelon-purple">•</span>
                  <span>Invested agents lose <span className="text-echelon-purple font-bold">-30 Sanity</span></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-echelon-amber">•</span>
                  <span>Founder's Yield stream ends <span className="text-echelon-amber font-bold">permanently</span></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-echelon-cyan">•</span>
                  <span>Connected timelines receive <span className="text-echelon-cyan font-bold">stability shock</span></span>
                </li>
              </ul>
            </div>
            
            <div className="bg-terminal-bg rounded p-3 mb-6">
              <span className="text-terminal-text-muted text-xs uppercase tracking-wide">Your Exposure</span>
              <div className="flex justify-between items-center mt-2">
                <span className="text-terminal-text">500 YES Shards</span>
                <span className="text-echelon-red font-bold">-$340.00 loss</span>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => setShowAbandonModal(false)}
                className="flex-1 px-4 py-3 bg-terminal-bg text-terminal-text rounded font-bold hover:bg-terminal-panel transition-colors"
              >
                CANCEL
              </button>
              <button 
                disabled
                className="flex-1 px-4 py-3 bg-echelon-red/20 border border-echelon-red/30 text-echelon-red/50 rounded font-bold cursor-not-allowed"
              >
                CONFIRM ABANDON
              </button>
            </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
