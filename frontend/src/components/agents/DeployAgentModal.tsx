/**
 * Deploy Agent Modal
 *
 * Showcase modal for deploying a new agent to a theatre.
 * Follows the TaskAgentModal pattern (glassmorphism overlay, bento layout).
 * Deploy button is disabled — requires wallet connection.
 */

import { useState, useEffect } from 'react';
import { X, Rocket, Zap, Activity, ShieldAlert, ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';
import { getArchetypeTheme, type Archetype } from '../../theme/agentsTheme';

interface DeployAgentModalProps {
  open: boolean;
  onClose: () => void;
}

const ARCHETYPES: { id: Archetype; name: string }[] = [
  { id: 'WHALE', name: 'Whale' },
  { id: 'DIPLOMAT', name: 'Diplomat' },
  { id: 'SABOTEUR', name: 'Saboteur' },
  { id: 'SHARK', name: 'Shark' },
  { id: 'SPY', name: 'Spy' },
];

const MOCK_THEATRES = [
  'ORB_SALVAGE_F7',
  'VEN_OIL_TANKER',
  'FED_RATE_DECISION',
  'TAIWAN_STRAIT',
  'NVDA_EARNINGS',
  'BTC_HALVING',
];

const STRATEGIES = ['Aggressive', 'Balanced', 'Defensive'] as const;

const CALLSIGN_PREFIXES = ['KRAKEN', 'PHANTOM', 'TITAN', 'NOVA', 'VORTEX', 'CIPHER', 'ONYX', 'APEX'];

function generateCallsign(): string {
  const prefix = CALLSIGN_PREFIXES[Math.floor(Math.random() * CALLSIGN_PREFIXES.length)];
  const suffix = Math.floor(Math.random() * 90) + 10;
  return `${prefix}-${suffix}`;
}

function getDeploymentCost(archetype: Archetype): { tokens: number; sanity: number; apy: string } {
  switch (archetype) {
    case 'WHALE':
      return { tokens: 500, sanity: 85, apy: '18-32%' };
    case 'DIPLOMAT':
      return { tokens: 300, sanity: 90, apy: '12-22%' };
    case 'SABOTEUR':
      return { tokens: 400, sanity: 70, apy: '25-45%' };
    case 'SHARK':
      return { tokens: 450, sanity: 75, apy: '22-40%' };
    case 'SPY':
      return { tokens: 350, sanity: 80, apy: '15-28%' };
    default:
      return { tokens: 250, sanity: 80, apy: '10-20%' };
  }
}

export function DeployAgentModal({ open, onClose }: DeployAgentModalProps) {
  const [selectedArchetype, setSelectedArchetype] = useState<Archetype | null>(null);
  const [agentName, setAgentName] = useState('');
  const [selectedTheatre, setSelectedTheatre] = useState(MOCK_THEATRES[0]);
  const [selectedStrategy, setSelectedStrategy] = useState<typeof STRATEGIES[number]>('Balanced');
  const [theatreOpen, setTheatreOpen] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setSelectedArchetype(null);
      setAgentName(generateCallsign());
      setSelectedTheatre(MOCK_THEATRES[0]);
      setSelectedStrategy('Balanced');
    }
  }, [open]);

  // Lock body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  if (!open) return null;

  const cost = selectedArchetype ? getDeploymentCost(selectedArchetype) : null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-terminal-bg/80 backdrop-blur-sm z-[300]"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-[310] flex items-center justify-center p-4 pointer-events-none"
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div
          className="bg-terminal-bg border border-glass-border rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-5 border-b border-glass-border flex items-center justify-between bg-glass-card backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-echelon-cyan/10 rounded-full flex items-center justify-center border border-echelon-cyan/20">
                <Rocket className="w-5 h-5 text-echelon-cyan" />
              </div>
              <div>
                <h3 className="text-white font-sans font-bold tracking-tight text-lg">DEPLOY AGENT</h3>
                <p className="text-terminal-text-muted text-xs font-sans">Select archetype, configure, and deploy to a theatre</p>
              </div>
            </div>
            <button onClick={onClose} className="text-terminal-text-muted hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-terminal-border scrollbar-track-transparent">

            {/* Step 1: Archetype Selection */}
            <div className="mb-6">
              <h4 className="text-xs font-sans font-semibold text-terminal-text-muted uppercase tracking-widest mb-4 ml-1">
                1. Choose Archetype
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {ARCHETYPES.map(({ id, name }) => {
                  const theme = getArchetypeTheme(id);
                  const Icon = theme.icon;
                  const isSelected = selectedArchetype === id;
                  return (
                    <button
                      key={id}
                      onClick={() => setSelectedArchetype(id)}
                      className={clsx(
                        'p-4 rounded-xl border text-left transition-all duration-200 group relative overflow-hidden',
                        isSelected
                          ? `${theme.bgClass} ${theme.borderClass} shadow-lg`
                          : 'bg-glass-card border-glass-border hover:border-terminal-border-light'
                      )}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <div className={clsx(
                          'w-10 h-10 rounded-lg flex items-center justify-center border transition-colors',
                          isSelected ? `${theme.bgClass} ${theme.borderClass}` : 'bg-white/5 border-white/10'
                        )}>
                          <Icon className={clsx(
                            'w-5 h-5 transition-colors',
                            isSelected ? theme.textClass : 'text-terminal-text-secondary group-hover:text-terminal-text'
                          )} />
                        </div>
                        <div>
                          <div className={clsx(
                            'font-sans font-semibold text-sm',
                            isSelected ? 'text-white' : 'text-terminal-text-secondary group-hover:text-white'
                          )}>
                            {name}
                          </div>
                          <div className="text-[10px] font-mono text-terminal-text-muted uppercase">{id}</div>
                        </div>
                      </div>
                      <p className="text-terminal-text-muted text-xs line-clamp-2 leading-relaxed">
                        {theme.description}
                      </p>
                      {isSelected && cost && (
                        <div className="flex items-center gap-3 mt-3 pt-2 border-t border-white/10">
                          <span className="text-echelon-amber text-xs font-mono flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            {cost.tokens} $ECH
                          </span>
                          <span className="text-echelon-green text-xs font-mono flex items-center gap-1">
                            <Activity className="w-3 h-3" />
                            {cost.sanity} SAN
                          </span>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Step 2: Configuration — only shown when archetype is selected */}
            {selectedArchetype && (
              <div className="mb-6 animate-fade-in">
                <h4 className="text-xs font-sans font-semibold text-terminal-text-muted uppercase tracking-widest mb-4 ml-1">
                  2. Configure Agent
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Agent Name */}
                  <div>
                    <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                      Callsign
                    </label>
                    <input
                      type="text"
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value.toUpperCase())}
                      className="w-full bg-terminal-bg border border-glass-border rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-terminal-text-muted focus:border-echelon-cyan/40 focus:outline-none focus:ring-1 focus:ring-echelon-cyan/20 transition-all"
                      placeholder="AGENT-XX"
                    />
                  </div>

                  {/* Theatre */}
                  <div>
                    <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                      Theatre
                    </label>
                    <div className="relative">
                      <button
                        onClick={() => setTheatreOpen(!theatreOpen)}
                        className="w-full flex items-center justify-between bg-terminal-bg border border-glass-border rounded-lg px-3 py-2 text-sm text-white font-mono hover:border-echelon-cyan/40 transition-all"
                      >
                        <span>{selectedTheatre}</span>
                        <ChevronDown className={clsx('w-4 h-4 text-terminal-text-muted transition', theatreOpen && 'rotate-180')} />
                      </button>
                      {theatreOpen && (
                        <>
                          <div className="fixed inset-0 z-10" onClick={() => setTheatreOpen(false)} />
                          <div className="absolute top-full left-0 mt-1 w-full bg-terminal-panel border border-terminal-border rounded-lg shadow-lg z-20 max-h-40 overflow-y-auto">
                            {MOCK_THEATRES.map((theatre) => (
                              <button
                                key={theatre}
                                onClick={() => { setSelectedTheatre(theatre); setTheatreOpen(false); }}
                                className={clsx(
                                  'w-full text-left px-3 py-2 text-xs font-mono hover:bg-terminal-card transition',
                                  selectedTheatre === theatre ? 'text-echelon-cyan' : 'text-terminal-text'
                                )}
                              >
                                {theatre}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Strategy */}
                  <div>
                    <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">
                      Strategy
                    </label>
                    <div className="flex gap-2">
                      {STRATEGIES.map((strategy) => (
                        <button
                          key={strategy}
                          onClick={() => setSelectedStrategy(strategy)}
                          className={clsx(
                            'flex-1 px-2 py-2 text-xs font-semibold rounded-lg border transition-all',
                            selectedStrategy === strategy
                              ? 'bg-echelon-cyan/10 border-echelon-cyan/30 text-echelon-cyan'
                              : 'bg-terminal-bg border-glass-border text-terminal-text-muted hover:text-terminal-text hover:border-terminal-border-light'
                          )}
                        >
                          {strategy}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Cost Summary */}
            {selectedArchetype && cost && (
              <div className="mb-4 animate-fade-in">
                <h4 className="text-xs font-sans font-semibold text-terminal-text-muted uppercase tracking-widest mb-4 ml-1">
                  3. Deployment Summary
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-terminal-text-muted font-sans">Deployment Cost</span>
                      <Zap className="w-4 h-4 text-echelon-amber opacity-80" />
                    </div>
                    <div className="text-xl font-mono font-bold text-echelon-amber tracking-tight">
                      {cost.tokens} $ECH
                    </div>
                  </div>

                  <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-terminal-text-muted font-sans">Est. APY Range</span>
                      <Activity className="w-4 h-4 text-echelon-green opacity-80" />
                    </div>
                    <div className="text-xl font-mono font-bold text-echelon-green tracking-tight">
                      {cost.apy}
                    </div>
                  </div>

                  <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-terminal-text-muted font-sans">Starting Sanity</span>
                      <ShieldAlert className="w-4 h-4 text-echelon-cyan opacity-80" />
                    </div>
                    <div className="text-xl font-mono font-bold text-echelon-cyan tracking-tight">
                      {cost.sanity}/100
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Wallet Warning Banner */}
            <div className="bg-echelon-amber/5 border border-echelon-amber/20 rounded-lg p-3 flex items-start gap-3">
              <ShieldAlert className="w-4 h-4 text-echelon-amber mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-echelon-amber text-sm font-bold font-sans">Wallet Connection Required</p>
                <p className="text-terminal-text-secondary text-xs mt-0.5 font-sans">
                  Connect wallet and hold $ECHELON to deploy autonomous agents.
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-5 border-t border-glass-border bg-glass-card backdrop-blur-md flex gap-3 rounded-b-xl">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-white/5 text-terminal-text-secondary rounded-lg font-bold hover:bg-white/10 transition-colors font-sans text-sm"
            >
              CANCEL
            </button>
            <button
              disabled
              className="flex-1 px-4 py-3 bg-echelon-cyan/10 border border-echelon-cyan/20 text-echelon-cyan/50 rounded-lg font-bold cursor-not-allowed flex items-center justify-center gap-2 font-sans text-sm"
            >
              <Rocket className="w-4 h-4" />
              CONNECT WALLET TO DEPLOY
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default DeployAgentModal;
