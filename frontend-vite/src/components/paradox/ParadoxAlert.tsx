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
      <div className="flex gap-2 mt-4">
        <button
          onClick={() => setShowExtractionModal(true)}
          className="flex-1 px-3 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded text-sm hover:bg-echelon-cyan/30 transition-colors flex items-center justify-center gap-2"
        >
          <Shield className="w-4 h-4" />
          EXTRACT
        </button>
        <button
          onClick={() => setShowAbandonModal(true)}
          className="px-3 py-2 bg-echelon-red/20 border border-echelon-red/50 text-echelon-red rounded text-sm hover:bg-echelon-red/30 transition-colors flex items-center justify-center gap-2"
        >
          <Skull className="w-4 h-4" />
          ABANDON
        </button>
      </div>

      {/* Extraction Modal */}
      {showExtractionModal && (
        <div 
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4"
          onClick={() => setShowExtractionModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-echelon-cyan/50 rounded-lg p-6 max-w-md w-full relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button 
              onClick={() => setShowExtractionModal(false)}
              className="absolute top-4 right-4 text-terminal-muted hover:text-terminal-text"
            >
              <X className="w-5 h-5" />
            </button>
            
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-echelon-cyan/20 rounded-full flex items-center justify-center">
                <Shield className="w-6 h-6 text-echelon-cyan" />
              </div>
              <div>
                <h3 className="text-echelon-cyan font-bold text-lg">EXTRACTION PROTOCOL</h3>
                <p className="text-terminal-muted text-xs">Deploy agent to contain paradox</p>
              </div>
            </div>
            
            {/* Paradox Info */}
            <div className="bg-echelon-red/20 border border-echelon-red/30 rounded p-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-echelon-red font-bold">{paradox.severity_class?.replace('CLASS_', '').replace('_', ' ') || 'CLASS_2_SEVERE'}</span>
                <span className="text-terminal-muted text-sm">Logic Gap: {((paradox.logic_gap || 0.45) * 100).toFixed(0)}%</span>
              </div>
              <p className="text-terminal-text text-sm mt-2">
                Timeline: <span className="text-terminal-text">{paradox.timeline_name || 'Unknown'}</span>
              </p>
            </div>
            
            {/* Cost Breakdown */}
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-terminal-muted">Extraction Cost</span>
                <span className="text-echelon-amber font-bold">{paradox.extraction_cost_echelon} $ECHELON</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-muted">Agent Sanity Cost</span>
                <span className="text-echelon-purple">-{paradox.carrier_sanity_cost} Sanity</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-muted">Success Probability</span>
                <span className="text-echelon-green">72%</span>
              </div>
              <div className="border-t border-terminal-border pt-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-terminal-muted">Reward on Success</span>
                  <span className="text-echelon-cyan font-bold">+250 $ECHELON + Rep</span>
                </div>
              </div>
            </div>
            
            {/* Warning */}
            <div className="bg-echelon-amber/20 border border-echelon-amber/30 rounded p-3 mb-6">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-echelon-amber mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-echelon-amber text-sm font-bold">Wallet Connection Required</p>
                  <p className="text-terminal-muted text-xs mt-1">
                    This feature requires a connected wallet and $ECHELON tokens. Available in full release Q1 2025.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex gap-3">
              <button 
                disabled
                className="flex-1 px-4 py-3 bg-echelon-cyan/20 border border-echelon-cyan/30 text-echelon-cyan/50 rounded cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Shield className="w-4 h-4" />
                CONNECT WALLET TO EXTRACT
              </button>
            </div>
            
            <p className="text-center text-terminal-muted text-xs mt-4">
              Join waitlist at <span className="text-echelon-cyan">playechelon.io</span>
            </p>
          </div>
        </div>
      )}

      {/* Abandon Modal */}
      {showAbandonModal && (
        <div 
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4"
          onClick={() => setShowAbandonModal(false)}
        >
          <div 
            className="bg-[#0D0D0D] border border-echelon-red/50 rounded-lg p-6 max-w-md w-full relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button 
              onClick={() => setShowAbandonModal(false)}
              className="absolute top-4 right-4 text-terminal-muted hover:text-terminal-text"
            >
              <X className="w-5 h-5" />
            </button>
            
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-echelon-red/20 rounded-full flex items-center justify-center">
                <Skull className="w-6 h-6 text-echelon-red" />
              </div>
              <div>
                <h3 className="text-echelon-red font-bold text-lg">ABANDON TIMELINE</h3>
                <p className="text-terminal-muted text-xs">Let the paradox detonate</p>
              </div>
            </div>
            
            {/* Warning */}
            <div className="bg-echelon-red/30 border border-echelon-red/50 rounded p-4 mb-4">
              <p className="text-echelon-red text-sm font-bold mb-2">⚠️ CATASTROPHIC CONSEQUENCES</p>
              <ul className="text-terminal-text text-sm space-y-1">
                <li>• All shards in this timeline will be <span className="text-echelon-red">BURNED</span></li>
                <li>• Invested agents lose <span className="text-echelon-purple">-30 Sanity</span></li>
                <li>• Founder's Yield stream ends permanently</li>
                <li>• Connected timelines receive stability shock</li>
              </ul>
            </div>
            
            {/* Your Exposure */}
            <div className="bg-terminal-bg rounded p-3 mb-6">
              <span className="text-terminal-muted text-xs">YOUR EXPOSURE IN THIS TIMELINE</span>
              <div className="flex justify-between items-center mt-2">
                <span className="text-terminal-text">500 YES Shards</span>
                <span className="text-echelon-red font-bold">-$340 loss</span>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex gap-3">
              <button 
                onClick={() => setShowAbandonModal(false)}
                className="flex-1 px-4 py-3 bg-terminal-bg border border-terminal-border text-terminal-text rounded hover:bg-terminal-panel transition-colors"
              >
                CANCEL
              </button>
              <button 
                disabled
                className="flex-1 px-4 py-3 bg-echelon-red/20 border border-echelon-red/30 text-echelon-red/50 rounded cursor-not-allowed"
              >
                CONFIRM ABANDON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
