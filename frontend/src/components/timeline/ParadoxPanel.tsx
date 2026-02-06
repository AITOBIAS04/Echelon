import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import type { TimelineParadoxStatus, ExtractionAttempt } from '../../types';

/**
 * ParadoxPanel Props
 */
export interface ParadoxPanelProps {
  /** Paradox status (null if no active paradox) */
  paradoxStatus: TimelineParadoxStatus | null;
  /** Current logic gap value */
  currentLogicGap: number;
  /** Callback when user clicks extract button */
  onExtract?: () => void;
}

/**
 * Format seconds to HH:MM:SS
 */
function formatCountdown(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format timestamp to HH:MM:SS
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  });
}

/**
 * Get severity badge styling
 */
function getSeverityStyles(severity: TimelineParadoxStatus['severity']) {
  switch (severity) {
    case 'CLASS_1_CRITICAL':
      return {
        bg: 'bg-echelon-red/20',
        border: 'border-echelon-red',
        text: 'text-red-500',
        pulse: 'animate-pulse',
      };
    case 'CLASS_2_SEVERE':
      return {
        bg: 'bg-orange-500/20',
        border: 'border-orange-500',
        text: 'text-orange-500',
        pulse: '',
      };
    case 'CLASS_3_MODERATE':
      return {
        bg: 'bg-echelon-amber/20',
        border: 'border-echelon-amber',
        text: 'text-amber-500',
        pulse: '',
      };
  }
}

/**
 * ParadoxPanel Component
 * 
 * Displays paradox status with countdown timer, extraction costs, and history.
 * Shows different states for no paradox vs active paradox.
 */
export function ParadoxPanel({
  paradoxStatus,
  currentLogicGap,
  onExtract,
}: ParadoxPanelProps) {
  const [countdown, setCountdown] = useState<number>(0);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Update countdown every second
  useEffect(() => {
    if (!paradoxStatus?.active) {
      setCountdown(0);
      return;
    }

    // Initialize countdown
    setCountdown(paradoxStatus.countdown);

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 0) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [paradoxStatus]);

  const hasParadox = paradoxStatus?.active === true;
  const distanceToThreshold = 60 - currentLogicGap;
  const isCriticalTime = countdown < 300; // Less than 5 minutes

  return (
    <div
      className={`bg-terminal-panel rounded-lg p-4 border ${
        hasParadox ? 'border-echelon-red' : 'border-green-500/50'
      }`}
    >
      {!hasParadox ? (
        // No Active Paradox State
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 border border-green-500 rounded">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-xs font-semibold text-green-500 uppercase">
              NO ACTIVE PARADOX
            </span>
          </div>
          <div className="text-sm text-terminal-text-muted">
            Distance to paradox: <span className="text-terminal-text font-mono">{distanceToThreshold.toFixed(1)}%</span>
          </div>
        </div>
      ) : (
        // Active Paradox State
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h3 className="text-lg font-bold text-terminal-text uppercase">
                PARADOX DETECTED
              </h3>
            </div>
            {paradoxStatus && (
              <div
                className={`px-3 py-1.5 rounded border ${
                  getSeverityStyles(paradoxStatus.severity).bg
                } ${
                  getSeverityStyles(paradoxStatus.severity).border
                } ${
                  getSeverityStyles(paradoxStatus.severity).text
                } ${
                  getSeverityStyles(paradoxStatus.severity).pulse
                }`}
              >
                <span className="text-xs font-semibold uppercase">
                  {paradoxStatus.severity.replace('CLASS_', 'CLASS ').replace('_', ' ')}
                </span>
              </div>
            )}
          </div>

          {/* Countdown */}
          <div className={`text-center ${isCriticalTime ? 'animate-pulse' : ''}`}>
            <div className="text-xs text-terminal-text-muted mb-1 uppercase tracking-wide">
              DETONATION IN:
            </div>
            <div className="text-3xl font-mono font-bold text-echelon-red">
              {formatCountdown(countdown)}
            </div>
          </div>

          {/* Trigger Info */}
          <div className="text-sm text-terminal-text-muted">
            Triggered by:{' '}
            <span className="text-terminal-text font-medium">
              {paradoxStatus.triggerReason.replace('_', ' ')}
            </span>{' '}
            at{' '}
            <span className="text-terminal-text font-mono">
              {paradoxStatus.triggerValue.toFixed(1)}%
            </span>
          </div>

          {/* Extraction Cost Breakdown */}
          {paradoxStatus && (
            <div className="bg-terminal-panel rounded p-3 space-y-2">
              <div className="text-xs text-terminal-text-muted uppercase mb-2">Extraction Cost</div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">USDC:</span>
                <span className="text-terminal-text font-mono">
                  ${paradoxStatus.extractionCost.usdc.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">$ECHELON:</span>
                <span className="text-terminal-text font-mono">
                  {paradoxStatus.extractionCost.echelon.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-text-muted">Sanity cost:</span>
                <span className="text-terminal-text font-mono">
                  {paradoxStatus.extractionCost.sanityCost}
                </span>
              </div>
            </div>
          )}

          {/* Current Carrier */}
          {paradoxStatus.carrierAgentId && paradoxStatus.carrierAgentName && (
            <div className="text-sm text-terminal-text-muted">
              Being carried by:{' '}
              <span className="text-terminal-text font-medium">
                {paradoxStatus.carrierAgentName}
              </span>
            </div>
          )}

          {/* Extract Button */}
          <button
            onClick={onExtract}
            disabled={!onExtract}
            className={`w-full py-3 px-4 rounded font-semibold text-sm uppercase transition ${
              onExtract
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'bg-terminal-card text-terminal-text-muted cursor-not-allowed'
            }`}
          >
            EXTRACT NOW
          </button>

          {/* Extraction History */}
          {paradoxStatus && paradoxStatus.extractionHistory.length > 0 && (
            <div>
              <button
                onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                className="flex items-center justify-between w-full text-sm text-terminal-text-muted hover:text-terminal-text transition"
              >
                <span>
                  Extraction History ({paradoxStatus.extractionHistory.length})
                </span>
                {isHistoryOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
              {isHistoryOpen && (
                <div className="mt-2 space-y-2">
                  {paradoxStatus.extractionHistory.map((attempt: ExtractionAttempt) => (
                    <div
                      key={attempt.timestamp}
                      className="flex items-center gap-2 text-xs bg-terminal-panel rounded p-2"
                    >
                      <span className="text-terminal-text-muted font-mono">
                        [{formatTime(attempt.timestamp)}]
                      </span>
                      <span className="text-terminal-text">{attempt.agentName}</span>
                      <span className="text-terminal-text-muted">—</span>
                      {attempt.success ? (
                        <span className="flex items-center gap-1 text-green-500">
                          <CheckCircle className="w-3 h-3" />
                          SUCCESS
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-red-500">
                          <XCircle className="w-3 h-3" />
                          FAILED
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
