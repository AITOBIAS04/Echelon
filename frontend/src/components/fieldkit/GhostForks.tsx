import { useState } from 'react';
import { GitBranch, Play, Pause, RotateCcw, Upload, Trash2, Zap } from 'lucide-react';
import { useTimelines } from '../../hooks/useWingFlaps';
import { clsx } from 'clsx';

interface GhostFork {
  id: string;
  name: string;
  baseTimeline: string;
  baseTimelineName: string;
  pivotPoint: string;
  createdAt: Date;
  status: 'running' | 'paused' | 'completed';
  virtualBalance: number;
  positions: GhostPosition[];
  pnl: number;
  pnlPercent: number;
}

interface GhostPosition {
  side: 'YES' | 'NO';
  shares: number;
  avgPrice: number;
  currentPrice: number;
}

// Demo ghost forks for demonstration
const DEMO_GHOST_FORKS: GhostFork[] = [
  {
    id: 'ghost_1',
    name: 'Fed Dovish Pivot',
    baseTimeline: 'TL_FED_RATE',
    baseTimelineName: 'Fed Rate Decision - January 2026',
    pivotPoint: 'What if Powell signals 50bps cut instead of 25bps?',
    createdAt: new Date(Date.now() - 3600000 * 2),
    status: 'running',
    virtualBalance: 10000,
    positions: [
      { side: 'YES', shares: 500, avgPrice: 0.65, currentPrice: 0.78 }
    ],
    pnl: 65,
    pnlPercent: 6.5
  },
  {
    id: 'ghost_2',
    name: 'Tanker Interdiction',
    baseTimeline: 'TL_GHOST_TANKER',
    baseTimelineName: 'Ghost Tanker - Venezuela Dark Fleet',
    pivotPoint: 'What if US Navy intercepts the tanker?',
    createdAt: new Date(Date.now() - 3600000 * 24),
    status: 'paused',
    virtualBalance: 10000,
    positions: [
      { side: 'NO', shares: 300, avgPrice: 0.30, currentPrice: 0.45 }
    ],
    pnl: -45,
    pnlPercent: -4.5
  }
];

export function GhostForks() {
  const { data: timelinesData } = useTimelines();
  const timelines = timelinesData?.timelines || [];
  
  const [ghostForks, setGhostForks] = useState<GhostFork[]>(DEMO_GHOST_FORKS);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTimeline, setSelectedTimeline] = useState<string>('');
  const [pivotPoint, setPivotPoint] = useState('');
  const [forkName, setForkName] = useState('');

  const handleCreateFork = () => {
    if (!selectedTimeline || !pivotPoint || !forkName) return;
    
    const timeline = timelines.find((t: any) => t.id === selectedTimeline);
    const newFork: GhostFork = {
      id: `ghost_${Date.now()}`,
      name: forkName,
      baseTimeline: selectedTimeline,
      baseTimelineName: timeline?.name || 'Unknown',
      pivotPoint,
      createdAt: new Date(),
      status: 'running',
      virtualBalance: 10000,
      positions: [],
      pnl: 0,
      pnlPercent: 0
    };
    
    setGhostForks([newFork, ...ghostForks]);
    setShowCreateModal(false);
    setSelectedTimeline('');
    setPivotPoint('');
    setForkName('');
  };

  const toggleForkStatus = (id: string) => {
    setGhostForks(forks => forks.map(f => 
      f.id === id 
        ? { ...f, status: f.status === 'running' ? 'paused' : 'running' }
        : f
    ));
  };

  const deleteFork = (id: string) => {
    setGhostForks(forks => forks.filter(f => f.id !== id));
  };

  const totalPnL = ghostForks.reduce((sum, fork) => sum + fork.pnl, 0);
  const totalPnLPercent = ghostForks.length > 0 ? (totalPnL / (ghostForks.length * 10000)) * 100 : 0;

  return (
    <div className="h-full flex flex-col overflow-y-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center flex-shrink-0">
        <div>
          <h3 className="text-status-info font-bold flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            GHOST FORKS
          </h3>
          <p className="text-terminal-text-secondary text-xs mt-1">
            Private simulations — test "what if" scenarios without real capital
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-status-info/20 border border-status-info text-status-info rounded hover:bg-status-info/30 transition-colors flex items-center gap-2"
        >
          <Zap className="w-4 h-4" />
          CREATE FORK
        </button>
      </div>

      {/* Virtual Balance Banner */}
      <div className="bg-gradient-to-r from-status-paradox/20 to-status-info/20 border border-status-paradox/30 rounded-lg p-4 flex-shrink-0">
        <div className="flex justify-between items-center w-full">
          <div>
            <span className="text-terminal-text-secondary text-sm">Simulation Balance</span>
            <div className="text-2xl font-bold text-terminal-text">$10,000.00</div>
            <span className="text-xs text-terminal-text-secondary">Virtual USDC — No real funds required</span>
          </div>
          <div className="text-right">
            <span className="text-terminal-text-secondary text-sm">Total Ghost P&L</span>
            <div className={clsx(
              'text-xl font-bold',
              totalPnL >= 0 ? 'text-status-success' : 'text-status-danger'
            )}>
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
            </div>
            <span className={clsx(
              'text-xs',
              totalPnLPercent >= 0 ? 'text-status-success' : 'text-status-danger'
            )}>
              {totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}% across all forks
            </span>
          </div>
        </div>
      </div>

      {/* Ghost Forks List */}
      {ghostForks.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-terminal-border rounded-lg flex-shrink-0">
          <GitBranch className="w-12 h-12 mx-auto mb-4 text-terminal-text-secondary" />
          <p className="text-terminal-text-secondary mb-4">No ghost forks yet</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="text-status-info hover:underline"
          >
            Create your first simulation →
          </button>
        </div>
      ) : (
        <div className="space-y-4 flex-shrink-0">
          {ghostForks.map(fork => (
            <div
              key={fork.id}
              className="terminal-card p-4 hover:border-status-info/50 transition-colors"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h4 className="text-terminal-text font-bold">{fork.name}</h4>
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-xs',
                      fork.status === 'running'
                        ? 'bg-status-success/20 text-status-success border border-status-success/30'
                        : 'bg-terminal-bg text-terminal-text-secondary border border-terminal-border'
                    )}>
                      {fork.status === 'running' ? '● LIVE' : '⏸ PAUSED'}
                    </span>
                  </div>
                  <p className="text-terminal-text-secondary text-xs mt-1">
                    Forked from: <span className="text-status-info">{fork.baseTimelineName}</span>
                  </p>
                </div>
                <div className="text-right">
                  <div className={clsx(
                    'text-lg font-bold',
                    fork.pnl >= 0 ? 'text-status-success' : 'text-status-danger'
                  )}>
                    {fork.pnl >= 0 ? '+' : ''}${fork.pnl.toFixed(2)} USDC
                  </div>
                  <div className={clsx(
                    'text-xs',
                    fork.pnl >= 0 ? 'text-status-success' : 'text-status-danger'
                  )}>
                    {fork.pnlPercent >= 0 ? '+' : ''}{fork.pnlPercent.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Pivot Point */}
              <div className="bg-status-warning/10 border border-status-warning/20 rounded p-3 mb-3">
                <span className="text-status-warning text-xs font-bold">PIVOT POINT:</span>
                <p className="text-terminal-text text-sm mt-1">{fork.pivotPoint}</p>
              </div>

              {/* Positions */}
              {fork.positions.length > 0 && (
                <div className="mb-3">
                  <span className="text-terminal-text-secondary text-xs">POSITIONS:</span>
                  <div className="flex gap-4 mt-2">
                    {fork.positions.map((pos, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <span className={clsx(
                          'px-2 py-0.5 rounded text-xs font-bold',
                          pos.side === 'YES'
                            ? 'bg-status-success/20 text-status-success'
                            : 'bg-status-danger/20 text-status-danger'
                        )}>
                          {pos.side}
                        </span>
                        <span className="text-terminal-text-secondary">{pos.shares} shares</span>
                        <span className="text-terminal-text-secondary">@</span>
                        <span className="text-terminal-text">${pos.avgPrice.toFixed(2)}</span>
                        <span className="text-terminal-text-secondary">→</span>
                        <span className={clsx(
                          pos.currentPrice > pos.avgPrice ? 'text-status-success' : 'text-status-danger'
                        )}>
                          ${pos.currentPrice.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-between items-center pt-3 border-t border-terminal-border">
                <div className="flex gap-2">
                  <button
                    onClick={() => toggleForkStatus(fork.id)}
                    className="p-2 text-terminal-text-secondary hover:text-status-info transition-colors"
                    title={fork.status === 'running' ? 'Pause' : 'Resume'}
                  >
                    {fork.status === 'running' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    className="p-2 text-terminal-text-secondary hover:text-status-warning transition-colors"
                    title="Reset Simulation"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteFork(fork.id)}
                    className="p-2 text-terminal-text-secondary hover:text-status-danger transition-colors"
                    title="Delete Fork"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <button
                  className="px-3 py-1.5 bg-status-paradox/20 border border-status-paradox/50 text-status-paradox rounded text-xs hover:bg-status-paradox/30 transition-colors flex items-center gap-2"
                  title="Publish this fork to global SIGINT"
                >
                  <Upload className="w-3 h-3" />
                  PUBLISH TO GLOBAL
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Fork Modal */}
      {showCreateModal && (
        <div 
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-[300] p-4"
          onClick={() => setShowCreateModal(false)}
        >
          <div 
            className="bg-terminal-overlay border border-echelon-cyan/50 rounded-lg p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-echelon-cyan font-bold text-lg mb-4 flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              CREATE GHOST FORK
            </h3>
            
            <div className="space-y-4">
              {/* Fork Name */}
              <div>
                <label className="text-terminal-text-muted text-sm block mb-2">Fork Name</label>
                <input
                  type="text"
                  value={forkName}
                  onChange={(e) => setForkName(e.target.value)}
                  placeholder="e.g., Fed Dovish Scenario"
                  className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-terminal-text focus:border-echelon-cyan outline-none"
                />
              </div>

              {/* Base Timeline */}
              <div>
                <label className="text-terminal-text-muted text-sm block mb-2">Fork From Timeline</label>
                <select
                  value={selectedTimeline}
                  onChange={(e) => setSelectedTimeline(e.target.value)}
                  className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-terminal-text focus:border-echelon-cyan outline-none"
                >
                  <option value="">Select a timeline...</option>
                  {timelines.map((t: any) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              {/* Pivot Point */}
              <div>
                <label className="text-terminal-text-muted text-sm block mb-2">
                  Pivot Point <span className="text-echelon-amber">(The "What If")</span>
                </label>
                <textarea
                  value={pivotPoint}
                  onChange={(e) => setPivotPoint(e.target.value)}
                  placeholder="What if the Fed cuts 50bps instead of 25bps?"
                  rows={3}
                  className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-terminal-text focus:border-echelon-cyan outline-none resize-none"
                />
              </div>

              {/* Virtual Balance Note */}
              <div className="bg-echelon-purple/20 border border-echelon-purple/30 rounded p-3 text-sm">
                <span className="text-echelon-purple">💰 Starting Balance:</span>
                <span className="text-terminal-text ml-2">$10,000 Virtual USDC</span>
                <p className="text-terminal-text-muted text-xs mt-1">
                  Test your strategy risk-free before committing real capital
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleCreateFork}
                disabled={!selectedTimeline || !pivotPoint || !forkName}
                className={clsx(
                  'flex-1 px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors',
                  selectedTimeline && pivotPoint && forkName
                    ? 'bg-echelon-cyan/20 border border-echelon-cyan text-echelon-cyan hover:bg-echelon-cyan/30'
                    : 'bg-terminal-bg border border-terminal-border text-terminal-text-muted cursor-not-allowed'
                )}
              >
                <Zap className="w-4 h-4" />
                CREATE SIMULATION
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-terminal-bg border border-terminal-border text-terminal-text-muted rounded hover:bg-terminal-panel transition-colors"
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

export default GhostForks;

