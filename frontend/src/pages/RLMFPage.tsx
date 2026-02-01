import { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Zap,
  Download,
  Play,
  ChevronRight
} from 'lucide-react';
import { useRlmfUi } from '../contexts/RlmfUiContext';

interface Position {
  option: string;
  size: number;
  timestamp: string;
  pnl: number;
}

interface ForkOption {
  id: string;
  label: string;
  price: number;
  probability: number;
  description: string;
  risk: 'LOW' | 'MED' | 'HIGH';
  time: number;
  selected: boolean;
}

export function RLMFPage() {
  const { viewMode } = useRlmfUi();
  const [epoch] = useState(184);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [forkTimer, setForkTimer] = useState(45);
  const [stability, setStability] = useState(87.3);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [betSizes, setBetSizes] = useState<{ [key: string]: number }>({ A: 0, B: 0, C: 0 });
  const [positions, setPositions] = useState<Position[]>([
    { option: 'A', size: 1200, timestamp: '14:28:33', pnl: 42 },
    { option: 'B', size: 850, timestamp: '14:27:15', pnl: -18 },
    { option: 'A', size: 400, timestamp: '14:25:42', pnl: 14 }
  ]);
  const [contribution, setContribution] = useState({ episodes: 47, vectors: 184, partners: 2 });
  const [agentThoughts, setAgentThoughts] = useState('Analyzing fork point options...');

  const forkOptions: ForkOption[] = [
    { id: 'A', label: 'OPTION A', price: 2.40, probability: 42, description: 'Stabilize rotation & secure debris.', risk: 'MED', time: 30, selected: selectedOption === 'A' },
    { id: 'B', label: 'OPTION B', price: 3.80, probability: 38, description: 'Cut and grab immediately.', risk: 'HIGH', time: 12, selected: selectedOption === 'B' },
    { id: 'C', label: 'OPTION C', price: 1.20, probability: 12, description: 'Wait for docking window.', risk: 'LOW', time: 120, selected: selectedOption === 'C' }
  ];

  const handleOptionSelect = useCallback((optionId: string) => {
    setSelectedOption(optionId);
    const messages: { [key: string]: string } = {
      A: '<span class="text-status-success">Evidence supports Option A. Stability preservation has highest expected value.</span>',
      B: '<span class="text-status-warning">Option B offers highest reward but elevated risk. Taking position.</span>',
      C: '<span class="text-status-info">Conservative approach warranted. Waiting for docking window.</span>'
    };
    setAgentThoughts(messages[optionId]);
  }, []);

  const updateBetSize = useCallback((option: string, size: number) => {
    setBetSizes(prev => ({ ...prev, [option]: size }));
  }, []);

  const placeBet = useCallback((option: string) => {
    const size = betSizes[option];
    if (size === 0) return;

    const optionData = forkOptions.find(o => o.id === option);
    if (!optionData) return;

    const newPosition: Position = {
      option,
      size,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      pnl: Math.round(size * optionData.price * 0.35 - size * 0.1)
    };

    setPositions(prev => [newPosition, ...prev]);
    setContribution(prev => ({ ...prev, episodes: prev.episodes + 1, vectors: prev.vectors + 4 }));
    setBetSizes(prev => ({ ...prev, [option]: 0 }));
  }, [betSizes, forkOptions]);

  const triggerSaboteur = useCallback(() => {
    setStability(prev => Math.max(0, prev - 15));
    setAgentThoughts('<span class="text-status-danger">⚠️ Sabotage detected! Re-evaluating position... Stability compromised.</span>');
    setTimeout(() => {
      setAgentThoughts('Analyzing fork point options...');
    }, 2000);
  }, []);

  const triggerParadox = useCallback(() => {
    setAgentThoughts('<span class="text-status-danger">💥 PARADOX EVENT: Logic gap critical. Timeline unstable.</span>');
    setTimeout(() => {
      setAgentThoughts('Analyzing fork point options...');
    }, 3000);
  }, []);

  // Timer effects
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timeInterval);
  }, []);

  useEffect(() => {
    const forkInterval = setInterval(() => {
      setForkTimer(prev => {
        if (prev <= 1) {
          const randomOption = ['A', 'B', 'C'][Math.floor(Math.random() * 3)];
          handleOptionSelect(randomOption);
          return 45;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(forkInterval);
  }, [handleOptionSelect]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalExposure = positions.reduce((sum, pos) => sum + pos.size, 0);

  const getOptionColor = (option: string) => {
    switch (option) {
      case 'A': return 'text-status-info bg-status-info/10 border-status-info';
      case 'B': return 'text-status-warning bg-status-warning/10 border-status-warning';
      case 'C': return 'text-status-paradox bg-status-paradox/10 border-status-paradox';
      default: return '';
    }
  };

  const getPnlColor = (pnl: number) => {
    return pnl >= 0 ? 'text-status-success' : 'text-status-danger';
  };

  return (
    <div className="h-full flex flex-col min-h-0">

      {/* Theatre Meta */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-terminal-text flex items-center gap-2">
              Orbital Salvage Echelon
              <span className="text-xs bg-status-info/10 text-status-info px-2 py-0.5 rounded border border-status-info/20 font-semibold">3D SPATIAL</span>
              <span className="text-xs bg-status-paradox/10 text-status-paradox px-2 py-0.5 rounded border border-status-paradox/20 font-semibold">MANIPULATION</span>
            </h2>
            <p className="text-terminal-muted text-xs mt-1">ID: orbital_salvage_v1 • Template: 3D-INERT • Diff: Standard</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wider font-semibold">Epoch</div>
              <div className="text-lg font-mono font-bold text-terminal-text">
                <span className="text-status-info">{epoch}</span>/250
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wider font-semibold">Elapsed</div>
              <div className="text-lg font-mono font-bold text-terminal-text">{formatTime(timeElapsed)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid - Independent Scrolling Columns */}
      <div className="flex-1 min-h-0 flex overflow-hidden gap-4">
        {/* Left Column Scroll Region */}
        <div className="flex-1 min-h-0 overflow-y-auto pr-2 custom-scrollbar">
          <div className="space-y-4 pb-2">
            {/* Live Telemetry Feed */}
            <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex justify-between items-center">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" />
                Live Telemetry Feed
              </span>
              <span className="text-xs font-mono text-terminal-muted">
                Fork #{epoch} in: <span className="text-status-warning font-semibold">{forkTimer}s</span>
              </span>
            </div>
            
            {/* Visualizer */}
            <div className="relative h-[240px] bg-[#050505] overflow-hidden">
              {/* Grid Background */}
              <div className="absolute inset-0 opacity-20" style={{
                backgroundImage: `linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)`,
                backgroundSize: '40px 40px'
              }} />

              {/* Radar sweep animation */}
              <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                <div className="absolute inset-0 rounded-full border border-status-info/10 animate-[spin_4s_linear_infinite]" />
                <div className="absolute top-1/2 left-1/2 w-[150px] h-px bg-gradient-to-r from-status-info/30 to-transparent origin-left animate-[spin_4s_linear_infinite]" />
              </div>

              {/* Radial Gradient Glow */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-status-info/5 rounded-full blur-3xl" />

              {/* Orbit Rings */}
              <div className="absolute top-1/2 left-1/2 w-[180px] h-[180px] -translate-x-1/2 -translate-y-1/2 border border-dashed border-terminal-border/40 rounded-full animate-[spin_60s_linear_infinite]" />
              <div className="absolute top-1/2 left-1/2 w-[240px] h-[240px] -translate-x-1/2 -translate-y-1/2 border border-terminal-border/20 rounded-full animate-[spin_40s_linear_infinite_reverse]" />

              {/* Corner brackets for terminal feel */}
              <div className="absolute top-3 left-3 w-6 h-6 border-l-2 border-t-2 border-status-info/30" />
              <div className="absolute top-3 right-3 w-6 h-6 border-r-2 border-t-2 border-status-info/30" />
              <div className="absolute bottom-3 left-3 w-6 h-6 border-l-2 border-b-2 border-status-info/30" />
              <div className="absolute bottom-3 right-3 w-6 h-6 border-r-2 border-b-2 border-status-info/30" />

              {/* Central Station (CSS Composite) */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                 <div className="relative">
                    <div className="w-16 h-16 border-2 border-status-info/50 bg-status-info/10 rounded-full animate-pulse flex items-center justify-center">
                       <div className="w-8 h-8 bg-status-info/20 rounded-full flex items-center justify-center">
                          <div className="w-2 h-2 bg-status-info rounded-full shadow-[0_0_10px_currentColor]" />
                       </div>
                    </div>
                    {/* Crosshairs */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-4 w-0.5 h-3 bg-status-info/50" />
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-4 w-0.5 h-3 bg-status-info/50" />
                    <div className="absolute left-0 top-1/2 -translate-x-4 -translate-y-1/2 w-3 h-0.5 bg-status-info/50" />
                    <div className="absolute right-0 top-1/2 translate-x-4 -translate-y-1/2 w-3 h-0.5 bg-status-info/50" />
                 </div>
              </div>

              {/* Agent Avatar (Floating) */}
              <div className="absolute top-[30%] right-[20%] animate-bounce duration-[3000ms]">
                <div className="relative">
                  <div className="w-8 h-8 bg-terminal-bg border border-status-paradox text-status-paradox rounded flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.3)] z-10">
                    <Zap className="w-4 h-4" />
                  </div>
                  <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[9px] font-mono text-status-paradox bg-terminal-bg/80 px-1 rounded border border-status-paradox/30 whitespace-nowrap">
                    AGENT: ACTIVE
                  </div>
                </div>
              </div>

              {/* Right HUD Panel */}
              <div className="absolute top-4 right-4 bg-terminal-bg/90 border border-terminal-border rounded p-3 backdrop-blur w-40">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-terminal-muted uppercase">Vector</span>
                    <span className="text-[10px] font-mono text-status-info">47.3°</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-terminal-muted uppercase">Bearing</span>
                    <span className="text-[10px] font-mono text-terminal-text">092°</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-terminal-muted uppercase">Range</span>
                    <span className="text-[10px] font-mono text-terminal-text">2.4km</span>
                  </div>
                  <div className="pt-2 border-t border-terminal-border/50">
                    <div className="flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
                      <span className="text-[9px] text-terminal-muted">TRACKING</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* HUD Overlay */}
              <div className="absolute top-4 left-4 bg-terminal-bg/90 border border-terminal-border rounded p-3 backdrop-blur shadow-xl w-48">
                <div className="space-y-3">
                  {/* Stability */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-[9px] font-bold text-terminal-text-muted uppercase tracking-wider">Sys. Stability</span>
                      <span className={`text-[10px] font-mono font-bold ${stability > 50 ? 'text-status-success' : 'text-status-danger'}`}>{stability.toFixed(1)}%</span>
                    </div>
                    <div className="h-1 bg-terminal-bg border border-terminal-border rounded-full overflow-hidden">
                      <div className={`h-full ${stability > 50 ? 'bg-status-success' : 'bg-status-danger'} transition-all duration-500`} style={{ width: `${stability}%` }} />
                    </div>
                  </div>

                   {/* Metrics Grid */}
                   <div className="grid grid-cols-2 gap-2 pt-2 border-t border-terminal-border/50">
                      <div>
                        <div className="text-[8px] text-terminal-muted uppercase">Logic Gap</div>
                        <div className="text-[10px] font-mono text-status-warning">12.4%</div>
                      </div>
                      <div>
                         <div className="text-[8px] text-terminal-muted uppercase">Entropy</div>
                         <div className="text-[10px] font-mono text-status-info">0.34</div>
                      </div>
                   </div>
                </div>
              </div>

              {/* Bottom Status Bar inside visualizer */}
              <div className="absolute bottom-0 left-0 right-0 h-8 bg-terminal-bg/80 border-t border-terminal-border backdrop-blur flex items-center px-4 justify-between text-[10px] font-mono">
                 <span className="text-terminal-muted">COORDS: <span className="text-terminal-text">47.22.91</span></span>
                 <span className="text-terminal-muted">STATUS: <span className="text-status-success animate-pulse">ONLINE</span></span>
              </div>
            </div>

            {/* Agent Thoughts */}
            <div className="p-3 border-b border-terminal-border">
              <div className="flex gap-3 bg-terminal-bg border-l-2 border-status-info rounded-r-lg p-2">
                <div className="w-5 h-5 bg-status-info/10 rounded flex items-center justify-center text-xs flex-shrink-0">🦈</div>
                <div>
                  <div className="text-xs font-semibold text-terminal-text">
                    MEGALODON <span className="text-terminal-muted font-normal text-[10px]">(SHARK ARCHETYPE)</span>
                  </div>
                  <div className="text-xs text-status-info mt-0.5" dangerouslySetInnerHTML={{ __html: agentThoughts }} />
                </div>
              </div>
            </div>

            {/* Fork Options - Market View only */}
            {viewMode === 'market' && (
            <div className="p-4">
              <div className="text-xs font-semibold text-terminal-muted uppercase tracking-wider mb-3">🎯 FORK POINT #{epoch} DECISION</div>
              <div className="grid grid-cols-3 gap-3">
                {forkOptions.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => handleOptionSelect(option.id)}
                    className={`p-3 bg-terminal-bg border rounded-lg text-left transition-all ${
                      option.selected 
                        ? option.id === 'A' ? 'border-status-info bg-status-info/5' :
                          option.id === 'B' ? 'border-status-warning bg-status-warning/5' :
                          'border-status-paradox bg-status-paradox/5'
                        : 'border-terminal-border hover:border-terminal-muted'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className={`text-xs font-bold uppercase tracking-wider ${
                        option.id === 'A' ? 'text-status-info' :
                        option.id === 'B' ? 'text-status-warning' :
                        'text-status-paradox'
                      }`}>{option.label}</span>
                      <span className="text-sm font-mono font-bold text-status-success">${option.price}</span>
                    </div>
                    <div className="text-xs text-terminal-text-secondary mb-2">{option.description}</div>
                    <div className="flex justify-between text-[10px] text-terminal-muted uppercase tracking-wider font-medium border-t border-terminal-border pt-2">
                      <span>Risk: {option.risk}</span>
                      <span>{option.time}s</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            )}
          </div>
          {/* End Live Telemetry Feed */}
        </div>

          {/* Betting Panel - Market View only */}
          {viewMode === 'market' && (
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-gradient-to-r from-status-info/10 to-transparent border-b border-status-info/20 flex justify-between items-center">
              <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5" />
                Place Your Bet
              </span>
              <span className="text-xs font-mono text-terminal-muted">Fork #{epoch}</span>
            </div>
            
            <div className="p-4 grid grid-cols-3 gap-3">
              {forkOptions.map((option) => (
                <div key={option.id} className={`bg-terminal-bg border rounded-lg p-3 flex flex-col ${
                  option.id === 'A' ? 'border-t-2 border-status-info' :
                  option.id === 'B' ? 'border-t-2 border-status-warning' :
                  'border-t-2 border-status-paradox'
                }`}>
                  <div className={`text-[10px] font-bold uppercase tracking-wider mb-2 ${
                    option.id === 'A' ? 'text-status-info' :
                    option.id === 'B' ? 'text-status-warning' :
                    'text-status-paradox'
                  }`}>{option.label}</div>
                  <div className="text-lg font-mono font-bold text-terminal-text mb-1">
                    ${option.price}
                    <span className="text-xs text-terminal-muted font-normal ml-1">({option.probability}%)</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="10000"
                    step="100"
                    value={betSizes[option.id]}
                    onChange={(e) => updateBetSize(option.id, parseInt(e.target.value))}
                    className="w-full h-1 bg-terminal-bg rounded-full appearance-none cursor-pointer border border-terminal-border mt-2 mb-1"
                  />
                  <div className="flex justify-between text-[10px] font-mono font-semibold text-terminal-text mb-2 pb-2 border-b border-dashed border-terminal-border">
                    <span>BET SIZE</span>
                    <span>${betSizes[option.id].toLocaleString()}</span>
                  </div>
                  <button
                    onClick={() => placeBet(option.id)}
                    disabled={betSizes[option.id] === 0}
                    className="mt-auto px-3 py-2 text-[10px] font-bold uppercase tracking-wider rounded border border-terminal-border text-terminal-muted transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:border-terminal-text hover:text-terminal-text hover:bg-terminal-panel"
                  >
                    {betSizes[option.id] > 0 ? `CONFIRM $${(betSizes[option.id] / 100).toFixed(0)} BET` : 'CONFIRM BET'}
                  </button>
                </div>
              ))}
            </div>

            {/* RLMF Narrative */}
            <div className="mx-4 mb-4 p-3 bg-gradient-to-br from-status-cyan/5 to-status-paradox/5 border border-status-cyan/15 rounded-lg flex items-center gap-3">
              <span className="text-lg">🤖</span>
              <span className="text-xs text-terminal-text-secondary">
                <strong className="text-status-cyan">Your bets create market prices → Market prices become reward signals → Reward signals train robot policies</strong>
              </span>
            </div>

            {/* Contribution Panel */}
            <div className="mx-4 mb-4 bg-terminal-bg border border-terminal-border rounded-lg p-3">
              <div className="text-[10px] font-semibold text-terminal-muted uppercase tracking-wider mb-3">📊 YOUR RLMF CONTRIBUTION</div>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-terminal-panel border border-terminal-border rounded p-2 text-center">
                  <div className="text-base font-mono font-bold text-terminal-text">{contribution.episodes}</div>
                  <div className="text-[9px] text-terminal-muted uppercase tracking-wider">Episodes</div>
                </div>
                <div className="bg-terminal-panel border border-terminal-border rounded p-2 text-center">
                  <div className="text-base font-mono font-bold text-terminal-text">{contribution.vectors}</div>
                  <div className="text-[9px] text-terminal-muted uppercase tracking-wider">Reward Vectors</div>
                </div>
                <div className="bg-terminal-panel border border-terminal-border rounded p-2 text-center">
                  <div className="text-base font-mono font-bold text-terminal-text">{contribution.partners}</div>
                  <div className="text-[9px] text-terminal-muted uppercase tracking-wider">Robot Partners</div>
                </div>
              </div>
            </div>

            {/* Positions */}
            <div className="mx-4 mb-4 bg-terminal-bg border border-terminal-border rounded-lg p-3">
              <div className="flex items-center justify-between mb-3">
                <div className="text-[10px] font-semibold text-terminal-muted uppercase tracking-wider">🎯 MY POSITIONS</div>
                <div className="text-xs font-mono text-status-info font-semibold">${totalExposure.toLocaleString()}</div>
</div>
              <div className="space-y-1.5">
                {positions.map((pos, index) => (
                  <div key={index} className="flex justify-between items-center p-1.5 bg-terminal-panel border border-terminal-border rounded">
                    <div className="flex gap-2 items-center">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${getOptionColor(pos.option)}`}>{pos.option}</span>
                      <span className="text-[10px] text-terminal-muted">{pos.timestamp}</span>
                    </div>
                    <div className="flex gap-3 items-center">
                      <span className="text-xs font-mono font-semibold">${pos.size.toLocaleString()}</span>
                      <span className={`text-xs font-mono font-semibold ${getPnlColor(pos.pnl)}`}>{pos.pnl >= 0 ? '+' : ''}{pos.pnl}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          )}

          {/* Fork Resolution Path */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Fork Resolution Path</span>
            </div>
            <div className="p-4">
              <div className="pl-3 border-l border-terminal-border ml-2 space-y-4">
                {[
                  { time: 'T+00:00', desc: 'Fork Triggered', status: 'done' },
                  { time: 'T+00:45', desc: 'Market Converges', status: 'active', detail: 'Option B: 62% | Option A: 28% | Option C: 10%' },
                  { time: 'T+01:00', desc: 'Action Executed', status: 'pending' },
                  { time: 'T+01:30', desc: 'Settlement', status: 'pending' }
                ].map((step, index) => (
                  <div key={index} className="relative pl-6">
                    <div className={`absolute left-[-5px] top-1 w-2.5 h-2.5 rounded-full transition-all ${
                      step.status === 'done' ? 'bg-status-success border-2 border-status-success' :
                      step.status === 'active' ? 'bg-status-info border-2 border-status-info shadow-[0_0_0_4px_rgba(59,130,246,0.15)]' :
                      'bg-terminal-panel border-2 border-terminal-border'
                    }`} />
                    <div className="text-xs font-mono font-semibold text-terminal-text">{step.time} — {step.desc}</div>
                    {step.detail && <div className="text-xs text-terminal-muted mt-0.5">{step.detail}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        {/* End Left Scroll Region */}

        {/* Right Column Scroll Region */}
        <div className="w-[360px] flex-shrink-0 min-h-0 overflow-y-auto pr-2 custom-scrollbar pb-2">
          {/* Reward Vector */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex justify-between items-center">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Reward Vector</span>
              <span className="text-xs font-mono text-status-info font-semibold">0.68</span>
            </div>
            <div className="p-4 space-y-3">
              {[
                { label: 'TIME EFFICIENCY', value: 0.72, color: 'bg-status-info' },
                { label: 'VALUE', value: 0.88, color: 'bg-status-success' },
                { label: 'COLLATERAL', value: 0.35, color: 'bg-status-warning' },
                { label: 'SAFETY', value: 0.91, color: 'bg-status-success' },
                { label: 'TRACE', value: 0.58, color: 'bg-status-paradox' }
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-[10px] text-terminal-muted uppercase tracking-wider font-medium mb-1">
                    <span>{item.label}</span>
                    <span className="font-mono">{item.value}</span>
                  </div>
                  <div className="h-1.5 bg-terminal-bg rounded-full overflow-hidden border border-terminal-border">
                    <div className={`h-full ${item.color} rounded-full shadow-[0_0_10px_rgba(0,0,0,0.3)]`} style={{ width: `${item.value * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Market Calibration */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Market Calibration</span>
            </div>
            <div className="p-4 space-y-2">
              <div className="text-[10px] text-terminal-muted border border-terminal-border rounded p-2 bg-terminal-bg mb-3">
                TARGETS: Brier &lt; 0.20 | ECE &lt; 0.10
              </div>
              <div className="flex justify-between items-center p-2 bg-terminal-bg border border-terminal-border rounded">
                <span className="text-xs text-terminal-text-secondary font-medium">Brier Score</span>
                <span className="text-xs font-mono font-semibold text-status-success">0.19</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-terminal-bg border border-terminal-border rounded">
                <span className="text-xs text-terminal-text-secondary font-medium">ECE (Error)</span>
                <span className="text-xs font-mono font-semibold text-status-success">0.06</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-terminal-bg border border-terminal-border rounded">
                <span className="text-xs text-terminal-text-secondary font-medium">Agent Accuracy</span>
                <span className="text-xs font-mono font-semibold text-status-info">67.3%</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-terminal-bg border border-terminal-border rounded">
                <span className="text-xs text-terminal-text-secondary font-medium">Sample Size</span>
                <span className="text-xs font-mono text-terminal-muted">12,847</span>
              </div>
            </div>
          </div>

          {/* Active Agents */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Active Agents (7)</span>
            </div>
            <div className="p-4 space-y-2">
              {[
                { label: 'SHARK (3)', percentage: 43, color: 'bg-status-info' },
                { label: 'SPY (2)', percentage: 29, color: 'bg-status-paradox' },
                { label: 'SABOT (1)', percentage: 14, color: 'bg-status-danger' },
                { label: 'DIPLO (1)', percentage: 14, color: 'bg-status-warning' }
              ].map((agent) => (
                <div key={agent.label} className="flex items-center gap-2">
                  <span className="text-[10px] text-terminal-text-secondary w-16">{agent.label}</span>
                  <div className="flex-1 h-1.5 bg-terminal-bg rounded-full overflow-hidden border border-terminal-border">
                    <div className={`h-full ${agent.color} rounded-full`} style={{ width: `${agent.percentage}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fork Market */}
          {viewMode === 'market' && (
            <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
                <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Fork Market</span>
              </div>
              <div className="p-2 space-y-1">
                {forkOptions.map((option) => (
                  <div key={option.id} className={`flex justify-between items-center p-2 rounded ${
                    option.id === 'A' ? 'bg-status-info/5 border border-status-info/20' :
                    option.id === 'B' ? 'bg-status-warning/5 border border-status-warning/20' :
                    'bg-status-paradox/5 border border-status-paradox/20'
                  }`}>
                    <span className={`text-xs font-medium ${
                      option.id === 'A' ? 'text-status-info' :
                      option.id === 'B' ? 'text-status-warning' :
                      'text-status-paradox'
                    }`}>{option.label}</span>
                    <div className="text-right">
                      <div className={`text-xs font-mono font-semibold ${
                        option.id === 'A' ? 'text-status-info' :
                        option.id === 'B' ? 'text-status-warning' :
                        'text-status-paradox'
                      }`}>{option.probability}%</div>
                      <div className="text-[9px] text-terminal-muted font-mono">${option.price}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RLMF Export */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">RLMF Export</span>
            </div>
            <div className="p-3">
              <div className="bg-terminal-bg border border-dashed border-terminal-border rounded p-3 mb-3">
                <div className="flex justify-between text-xs text-terminal-text-secondary mb-2">
                  <span>Sampling Rate</span>
                  <span className="font-mono">50%</span>
                </div>
                <input type="range" min="0" max="100" defaultValue="50" className="w-full mb-3 h-1 bg-terminal-bg rounded-full appearance-none cursor-pointer border border-terminal-border" />
                <div className="flex justify-between text-xs text-terminal-text-secondary mb-2">
                  <span>Format</span>
                  <select className="bg-terminal-bg border border-terminal-border rounded px-2 py-0.5 text-xs outline-none">
                    <option>PyTorch (.pt)</option>
                    <option>JSON</option>
                  </select>
                </div>
                <button className="w-full py-2 bg-terminal-panel border border-status-info text-status-info rounded text-[10px] font-bold uppercase tracking-wider hover:bg-status-info/10 transition-colors flex items-center justify-center gap-1">
                  <Download className="w-3 h-3" /> Export Data
                </button>
              </div>
              <div className="bg-terminal-bg border border-terminal-border rounded p-2 font-mono text-[9px] text-terminal-muted leading-relaxed overflow-x-auto">
{`{
  "episode_id": "uuid-184",
  "reward": { "time": 0.72, "val": 0.88 },
  "calib": { "brier": 0.19 }
}`}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
              <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Actions</span>
            </div>
            <div className="p-2 grid grid-cols-2 gap-2">
              <button className="py-2 px-3 bg-terminal-bg border border-terminal-border rounded text-xs text-terminal-text-secondary font-medium hover:bg-terminal-panel hover:border-terminal-muted transition-colors flex items-center justify-center gap-1">
                <Play className="w-3 h-3" /> Override
              </button>
              <button className="py-2 px-3 bg-terminal-bg border border-terminal-border rounded text-xs text-terminal-text-secondary font-medium hover:bg-terminal-panel hover:border-terminal-muted transition-colors flex items-center justify-center gap-1">
                <ChevronRight className="w-3 h-3" /> Skip Fork
              </button>
              <button onClick={triggerSaboteur} className="py-2 px-3 bg-terminal-bg border border-status-danger/30 rounded text-xs text-status-danger font-medium hover:bg-status-danger/10 transition-colors flex items-center justify-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Inject Saboteur
              </button>
              <button onClick={triggerParadox} className="py-2 px-3 bg-terminal-bg border border-status-danger/30 rounded text-xs text-status-danger font-medium hover:bg-status-danger/10 transition-colors flex items-center justify-center gap-1">
                <Zap className="w-3 h-3" /> Force Paradox
              </button>
            </div>
          </div>
        </div>
        {/* End Right Scroll Region */}
      </div>
    </div>
  );
}
