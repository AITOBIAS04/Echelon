import { useState, useEffect, useCallback } from 'react';
import { Activity, CheckCircle, Clock, ExternalLink, Zap } from 'lucide-react';

interface VRFRequest {
  id: string;
  hash: string;
  block: number;
  type: string;
  status: 'verified' | 'pending' | 'failed';
  timestamp: string;
}

interface AuditEntry {
  time: string;
  type: string;
  detail: string;
  color: 'positive' | 'info' | 'warning' | 'danger';
}

export function VRFPage() {
  const [currentHash, setCurrentHash] = useState<string>('');
  const [requests, setRequests] = useState<VRFRequest[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [stats] = useState({
    totalRequests: 47892,
    verificationRate: 99.97,
    avgResponseTime: 2.3,
    entropyQuality: 9.8
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const generateHash = useCallback(() => {
    const chars = '0123456789abcdef';
    let hash = '0x';
    for (let i = 0; i < 64; i++) {
      hash += chars[Math.floor(Math.random() * chars.length)];
    }
    return hash;
  }, []);

  const generateShortHash = (hash: string) => {
    return `${hash.substring(0, 6)}...${hash.substring(58)}`;
  };

  const generateRequest = useCallback((): VRFRequest => {
    const hash = generateHash();
    const usageTypes = ['Sabotage Exec', 'Episode Samp', 'Circuit Breaker', 'Data Valid', 'Entropy Pricing', 'Fork Selection'];
    const type = usageTypes[Math.floor(Math.random() * usageTypes.length)];
    const statusRoll = Math.random();
    let status: 'verified' | 'pending' | 'failed' = 'verified';
    if (statusRoll > 0.97 + 0.02) {
      status = 'failed';
    } else if (statusRoll > 0.97) {
      status = 'pending';
    }
    return {
      id: generateShortHash(hash),
      hash,
      block: 2847000 + Math.floor(Math.random() * 500),
      type,
      status,
      timestamp: new Date().toISOString().split('T')[1].slice(0, 8)
    };
  }, [generateHash]);

  const addAuditEntry = useCallback(() => {
    const events = [
      { type: 'VRF Request Fulfilled', color: 'positive' as const, detail: 'Request fulfilled with proof verification' },
      { type: 'Block Hash Confirmed', color: 'info' as const, detail: 'Parent block hash finalized on-chain' },
      { type: 'Data Validation', color: 'positive' as const, detail: 'Feed validated at VRF checkpoint' },
      { type: 'Circuit Breaker Updated', color: 'info' as const, detail: 'Threshold randomized via VRF' },
      { type: 'Entropy Calculation', color: 'warning' as const, detail: 'Dynamic pricing updated' }
    ];
    const event = events[Math.floor(Math.random() * events.length)];
    const time = new Date().toISOString().split('T')[1].slice(0, 8);
    
    setAuditTrail(prev => {
      const newEntry: AuditEntry = { ...event, time };
      const updated = [newEntry, ...prev.slice(0, 9)];
      return updated;
    });
  }, []);

  const updateHistory = useCallback(() => {
    setRequests(prev => {
      const newRequest = generateRequest();
      const updated = [newRequest, ...prev.slice(0, 9)];
      return updated;
    });
  }, [generateRequest]);

  const refreshDashboard = useCallback(() => {
    setIsRefreshing(true);
    setCurrentHash(generateHash());
    addAuditEntry();
    updateHistory();
    setTimeout(() => setIsRefreshing(false), 500);
  }, [generateHash, addAuditEntry, updateHistory]);

  useEffect(() => {
    const initialHash = generateHash();
    setCurrentHash(initialHash);
    
    const initialRequests: VRFRequest[] = Array.from({ length: 5 }, () => generateRequest());
    setRequests(initialRequests);

    const initialAudit: AuditEntry[] = [
      { time: '14:32:22', type: 'VRF Request Fulfilled', detail: 'Request ID 0x8f7b...a5f4 fulfilled with proof 0x3a8f...2d4c', color: 'positive' },
      { time: '14:32:20', type: 'Circuit Breaker Updated', detail: 'Stability delta threshold set to 12.3% (VRF +2.3%)', color: 'info' },
      { time: '14:32:18', type: 'VRF Request Initiated', detail: 'New request sent to Chainlink VRF Coordinator', color: 'warning' },
      { time: '14:32:15', type: 'Data Validation Complete', detail: 'Market data feed validated (VRF checkpoint #1,247)', color: 'positive' }
    ];
    setAuditTrail(initialAudit);
  }, [generateHash, generateRequest]);

  useEffect(() => {
    const auditInterval = setInterval(addAuditEntry, 3000);
    const historyInterval = setInterval(updateHistory, 10000);
    return () => {
      clearInterval(auditInterval);
      clearInterval(historyInterval);
    };
  }, [addAuditEntry, updateHistory]);

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'verified':
        return <span className="w-1.5 h-1.5 bg-status-success rounded-full shadow-[0_0_4px_rgba(74,222,128,0.4)]" />;
      case 'pending':
        return <span className="w-1.5 h-1.5 bg-status-warning rounded-full" />;
      case 'failed':
        return <span className="w-1.5 h-1.5 bg-status-danger rounded-full" />;
      default:
        return null;
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-muted uppercase tracking-wider font-semibold mb-2">Total VRF Requests</div>
          <div className="text-2xl font-mono font-bold text-terminal-text">{formatNumber(stats.totalRequests)}</div>
          <div className="text-xs text-terminal-muted mt-1">Since network launch</div>
          <div className="text-xs text-status-success mt-2 flex items-center gap-1">
            <span>↑ 12.4% this week</span>
          </div>
        </div>
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-muted uppercase tracking-wider font-semibold mb-2">Verification Rate</div>
          <div className="text-2xl font-mono font-bold text-status-success">{stats.verificationRate}%</div>
          <div className="text-xs text-terminal-muted mt-1">On-chain success</div>
          <div className="text-xs text-status-success mt-2 flex items-center gap-1">
            <span>↑ 0.02% from last month</span>
          </div>
        </div>
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-muted uppercase tracking-wider font-semibold mb-2">Avg Response Time</div>
          <div className="text-2xl font-mono font-bold text-terminal-text">{stats.avgResponseTime}s</div>
          <div className="text-xs text-terminal-muted mt-1">Block to fulfillment</div>
          <div className="text-xs text-status-success mt-2 flex items-center gap-1">
            <span>↓ 0.4s improvement</span>
          </div>
        </div>
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-muted uppercase tracking-wider font-semibold mb-2">Entropy Quality</div>
          <div className="text-2xl font-mono font-bold text-status-entropy">{stats.entropyQuality}/10</div>
          <div className="text-xs text-terminal-muted mt-1">NIST randomness score</div>
          <div className="text-xs text-terminal-text-secondary mt-2">
            Stable
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-status-vrf" />
          <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">Current Randomness State</h2>
        </div>
        <span className="text-xsbg-status-vrf/10 text-status-vrf px-2 py-1 rounded border border-status-vrf/30 font-semibold">CHAINLINK VRF V2</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex justify-between items-center">
            <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Latest Request #47,893</span>
          </div>
          <div className="p-4 space-y-4">
            <div className="bg-terminal-bg border border-terminal-border rounded-lg p-4 font-mono text-xs">
              <div className="text-status-vrf break-all leading-relaxed">{currentHash || generateHash()}</div>
              <div className="flex gap-4 mt-3 pt-3 border-t border-terminal-border border-dashed text-terminal-muted text-xs">
                <span>ID: {generateShortHash(currentHash || generateHash())}</span>
                <span>BLK: #2,847,392</span>
                <span>TS: 14:32:18 UTC</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-3 p-2.5 bg-terminal-bg border border-terminal-border rounded-lg">
                <div className="w-5 h-5 rounded-full bg-status-success/10 flex items-center justify-center text-status-success text-xs">✓</div>
                <div>
                  <div className="text-xs font-medium text-terminal-text">Block Hash Verification</div>
                  <div className="text-xs text-terminal-muted">Parent block hash cryptographically verified</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-2.5 bg-terminal-bg border border-terminal-border rounded-lg">
                <div className="w-5 h-5 rounded-full bg-status-success/10 flex items-center justify-center text-status-success text-xs">✓</div>
                <div>
                  <div className="text-xs font-medium text-terminal-text">Proof Validation</div>
                  <div className="text-xs text-terminal-muted">VRF proof successfully validated on-chain</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-2.5 bg-terminal-bg border border-terminal-border rounded-lg">
                <div className="w-5 h-5 rounded-full bg-status-success/10 flex items-center justify-center text-status-success text-xs">✓</div>
                <div>
                  <div className="text-xs font-medium text-terminal-text">Output Range Check</div>
                  <div className="text-xs text-terminal-muted">Random output within valid range [0, 2^256-1]</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-2.5 bg-terminal-bg border border-terminal-border rounded-lg">
                <div className="w-5 h-5 rounded-full bg-status-info/10 flex items-center justify-center text-status-info text-xs">⟳</div>
                <div>
                  <div className="text-xs font-medium text-terminal-text">Execution Window</div>
                  <div className="text-xs text-terminal-muted">30-60s window starting in 18s</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
            <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">VRF-Enhanced Circuit Breakers</span>
          </div>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-terminal-bg border border-status-success/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-status-success" />
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Stability Delta</div>
                <div className="text-lg font-mono font-bold text-terminal-text">
                  10.0% <span className="text-status-vrf text-xs">+VRF</span>
                </div>
                <div className="text-xs text-status-vrf font-mono mt-1">Randomized: +2.3%</div>
              </div>
              <div className="bg-terminal-bg border border-status-success/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-status-success" />
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Paradox Threshold</div>
                <div className="text-lg font-mono font-bold text-terminal-text">
                  40.0% <span className="text-status-vrf text-xs">+VRF</span>
                </div>
                <div className="text-xs text-status-vrf font-mono mt-1">Randomized: +6.7%</div>
              </div>
              <div className="bg-terminal-bg border border-status-success/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-status-success" />
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Max Scaling</div>
                <div className="text-lg font-mono font-bold text-terminal-text">
                  2.5x <span className="text-status-vrf text-xs">+VRF</span>
                </div>
                <div className="text-xs text-status-vrf font-mono mt-1">Randomized: +0.4x</div>
              </div>
              <div className="bg-terminal-bg border border-status-success/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-status-success" />
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Sabotage Cool</div>
                <div className="text-lg font-mono font-bold text-terminal-text">
                  300s <span className="text-status-vrf text-xs">+VRF</span>
                </div>
                <div className="text-xs text-status-vrf font-mono mt-1">Randomized: +42s</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-terminal-bg border border-terminal-border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-[#375bd2] text-white flex items-center justify-center font-bold text-xs">CL</div>
                <div>
                  <div className="text-xs font-medium text-terminal-text">Chainlink VRF Coordinator</div>
                  <div className="text-xs text-terminal-muted font-mono">0xf0d...4e21 - Base Mainnet</div>
                </div>
              </div>
              <div className="flex gap-4 text-right">
                <div>
                  <div className="text-xs font-mono font-semibold text-status-success">99.99%</div>
                  <div className="text-[9px] text-terminal-muted uppercase">UPTIME</div>
                </div>
                <div>
                  <div className="text-xs font-mono font-semibold">12,847</div>
                  <div className="text-[9px] text-terminal-muted uppercase">GAS AVG</div>
                </div>
                <div>
                  <div className="text-xs font-mono font-semibold">V2</div>
                  <div className="text-[9px] text-terminal-muted uppercase">VER</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-status-info" />
          <span className="text-sm font-semibold text-terminal-text uppercase tracking-wider">VRF-Backed Market Data Validation</span>
        </div>
        <div className="p-4">
          <p className="text-xs text-terminal-text-secondary mb-4">
            VRF-randomized data validation sampling prevents predictable manipulation patterns. Each feed is validated using VRF-selected checkpoints.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { name: 'Market Data', confidence: 98.2, color: 'bg-status-success' },
              { name: 'On-Chain', confidence: 99.1, color: 'bg-status-success' },
              { name: 'News/Sentiment', confidence: 94.7, color: 'bg-status-warning' },
              { name: 'Browser Auto', confidence: 91.3, color: 'bg-status-warning' },
              { name: 'Maritime (AIS)', confidence: 96.5, color: 'bg-status-success' },
              { name: 'Aviation (ADS-B)', confidence: 95.8, color: 'bg-status-success' }
            ].map((item) => (
              <div key={item.name} className="bg-terminal-bg border border-terminal-border rounded-lg p-3 text-center">
                <div className="text-xs font-medium text-terminal-text mb-2">{item.name}</div>
                <span className="text-[9px] text-status-vrf bg-status-vrf/10 px-1.5 py-0.5 rounded border border-status-vrf/20">&lt;&gt; VRF Secured</span>
                <div className="h-1 bg-terminal-bg rounded-full mt-2 mb-1 overflow-hidden border border-terminal-border">
                  <div className={`h-full ${item.color} rounded-full transition-all duration-500`} style={{ width: `${item.confidence}%` }} />
                </div>
                <div className="text-[9px] text-terminal-muted font-mono">{item.confidence.toFixed(1)}% confidence</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-status-vrf/5 to-status-entropy/5 pointer-events-none" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-status-vrf" />
              RLMF Validation Framework
            </h3>
            <span className="text-xs text-terminal-muted font-mono">Last updated: 14:32:22 UTC</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 text-center">
              <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Total Episodes</div>
              <div className="text-xl font-mono font-bold text-status-vrf">12,847</div>
              <div className="text-[10px] text-terminal-muted mt-1">Fork decisions analyzed</div>
            </div>
            <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 text-center">
              <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">VRF-Sampled</div>
              <div className="text-xl font-mono font-bold text-status-vrf">1,285</div>
              <div className="text-[10px] text-terminal-muted mt-1">10% random checkpoint</div>
            </div>
            <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 text-center">
              <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Calibration</div>
              <div className="text-xl font-mono font-bold text-status-vrf">0.18</div>
              <div className="text-[10px] text-terminal-muted mt-1">Brier Score (target: &lt;0.20)</div>
            </div>
            <div className="bg-terminal-bg border border-status-success/30 rounded-lg p-3 text-center">
              <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Integrity</div>
              <div className="text-xl font-mono font-bold text-status-success">100%</div>
              <div className="text-[10px] text-terminal-muted mt-1">All exports verified</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex justify-between items-center">
            <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Recent VRF Requests</span>
            <button className="text-xs text-terminal-muted hover:text-terminal-text transition-colors flex items-center gap-1">
              View All <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-terminal-border bg-terminal-bg">
                  <th className="text-left px-4 py-2 font-semibold text-terminal-muted uppercase tracking-wider text-[10px]">Request ID</th>
                  <th className="text-left px-4 py-2 font-semibold text-terminal-muted uppercase tracking-wider text-[10px]">Block</th>
                  <th className="text-left px-4 py-2 font-semibold text-terminal-muted uppercase tracking-wider text-[10px]">Type</th>
                  <th className="text-left px-4 py-2 font-semibold text-terminal-muted uppercase tracking-wider text-[10px]">Status</th>
                  <th className="text-right px-4 py-2 font-semibold text-terminal-muted uppercase tracking-wider text-[10px]">Time</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((request, index) => (
                  <tr key={index} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-status-vrf">{request.id}</td>
                    <td className="px-4 py-2.5 font-mono text-terminal-muted">#{request.block.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-terminal-text-secondary">{request.type}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        {getStatusDot(request.status)}
                        <span className="capitalize text-terminal-text-secondary">{request.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-terminal-muted text-right">{request.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex items-center gap-2">
            <Clock className="w-4 h-4 text-terminal-muted" />
            <span className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">Live Audit Trail</span>
          </div>
          <div className="max-h-[280px] overflow-y-auto">
            {auditTrail.map((entry, index) => (
              <div key={index} className="flex gap-3 px-4 py-2.5 border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                <div className="font-mono text-xs text-terminal-muted min-w-[70px]">{entry.time}</div>
                <div>
                  <div className={`text-xs font-semibold ${
                    entry.color === 'positive' ? 'text-status-success' :
                    entry.color === 'info' ? 'text-status-info' :
                    entry.color === 'warning' ? 'text-status-warning' :
                    'text-status-danger'
                  }`}>{entry.type}</div>
                  <div className="text-xs text-terminal-text-secondary mt-0.5">{entry.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-terminal-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-terminal-muted">
        <div>Echelon Protocol VRF Dashboard - Base Mainnet</div>
        <div className="flex gap-4">
          <a href="#" className="text-terminal-text-secondary hover:text-terminal-text transition-colors">Documentation</a>
          <a href="#" className="text-terminal-text-secondary hover:text-terminal-text transition-colors">Audit Reports</a>
          <a href="#" className="text-terminal-text-secondary hover:text-terminal-text transition-colors">Smart Contracts</a>
        </div>
      </div>
    </div>
  );
}
