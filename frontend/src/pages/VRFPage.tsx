/**
 * VRF Integrity Terminal
 *
 * Audit-grade dashboard showing how Chainlink VRF protects 6 specific
 * integrity mechanisms in the Echelon LMSR/CFPM protocol.
 *
 *   1. Entropy Commitments — infra SLO stat cards + commitment hash
 *   2. Where VRF Is Applied — 6 application point cards with drawer
 *   3. LMSR Integrity Coupling — anti-manipulation + cost-to-move widget
 *   4. Status strip + filterable Audit Trail
 *
 * All data is demo/simulated — no live Chainlink integration.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Shield, Zap, Timer, ShieldAlert, Database, Brain, Coins, Server,
  Lock, Clock, Search, X, Copy,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import { lmsrCost, LIQUIDITY_B } from '../lib/lmsr';

// ── Types ───────────────────────────────────────────────────────────────

type VRFComponent =
  | 'commit-reveal'
  | 'circuit-breaker'
  | 'data-validation'
  | 'rlmf-sampling'
  | 'entropy-pricing'
  | 'oracle-failover';

interface ApplicationPoint {
  id: VRFComponent;
  name: string;
  description: string;
  icon: LucideIcon;
  lastDraw: { timestamp: string; requestId: string };
  result: string;
}

interface AuditEntry {
  id: string;
  time: string;
  component: VRFComponent;
  requestId: string;
  blockTx: string;
  derivedEffect: string;
  status: 'verified' | 'pending' | 'failed';
}

interface AuditFilters {
  component: VRFComponent | 'all';
  status: 'verified' | 'pending' | 'failed' | 'all';
}

interface AuditDrawerData {
  component: VRFComponent;
  name: string;
  description: string;
  icon: LucideIcon;
  requestId: string;
  shortRequestId: string;
  blockTx: string;
  seed: string;
  proofStatus: 'verified' | 'pending';
  derivedEffect: string;
  timestamp: string;
}

// ── Constants ───────────────────────────────────────────────────────────

const COMMITMENT_HASH = '0x7a3f8b2c1d9e4f6a0b5c3d7e8f1a2b4c6d8e0f1a2b3c4d5e6f7a8b9c0d1ecb18';

const COMPONENT_LABELS: Record<VRFComponent, string> = {
  'commit-reveal': 'Commit-Reveal Window',
  'circuit-breaker': 'Circuit Breaker',
  'data-validation': 'Data Validation',
  'rlmf-sampling': 'RLMF Sampling',
  'entropy-pricing': 'Risk Fee Jitter',
  'oracle-failover': 'Oracle Failover',
};

const COMPONENTS: VRFComponent[] = [
  'commit-reveal', 'circuit-breaker', 'data-validation',
  'rlmf-sampling', 'entropy-pricing', 'oracle-failover',
];

const INITIAL_APPLICATION_POINTS: ApplicationPoint[] = [
  {
    id: 'commit-reveal',
    name: 'Commit-Reveal Window',
    description: 'Randomised execution window (30\u201360s) prevents timing attacks on sabotage actions.',
    icon: Timer,
    lastDraw: { timestamp: '14:32:18 UTC', requestId: '0x8f7b...a5f4' },
    result: 'Delay chosen: +37s',
  },
  {
    id: 'circuit-breaker',
    name: 'Circuit Breaker Thresholds',
    description: 'Randomised offset on base thresholds prevents threshold manipulation and predictable triggering.',
    icon: ShieldAlert,
    lastDraw: { timestamp: '14:31:45 UTC', requestId: '0x3a8f...2d4c' },
    result: 'Threshold offset: +2.3%',
  },
  {
    id: 'data-validation',
    name: 'Market Data Validation',
    description: 'Random feed sampling selection prevents predictable validation gaming across OSINT sources.',
    icon: Database,
    lastDraw: { timestamp: '14:30:12 UTC', requestId: '0xd4e1...8b7a' },
    result: 'Feeds sampled: 3/6',
  },
  {
    id: 'rlmf-sampling',
    name: 'RLMF Episode Sampling',
    description: 'Verifiable random episode selection ensures unbiased training data for reinforcement learning.',
    icon: Brain,
    lastDraw: { timestamp: '14:29:33 UTC', requestId: '0x7c2d...f1e9' },
    result: 'Episodes sampled: 128',
  },
  {
    id: 'entropy-pricing',
    name: 'Risk Fee Jitter',
    description: 'Randomised risk fee adjustment prevents fee prediction gaming on sabotage pricing.',
    icon: Coins,
    lastDraw: { timestamp: '14:28:05 UTC', requestId: '0xb5a3...6c8d' },
    result: 'Fee multiplier: 1.14x',
  },
  {
    id: 'oracle-failover',
    name: 'Oracle Failover',
    description: 'Randomised failover provider selection prevents oracle targeting attacks in degraded modes.',
    icon: Server,
    lastDraw: { timestamp: '14:27:41 UTC', requestId: '0xe9f0...4a2b' },
    result: 'Provider: Primary',
  },
];

const ANTI_MANIPULATION_SURFACES = [
  { label: 'Timing Fairness', desc: 'VRF-randomised commit\u2013reveal windows prevent front-running sabotage execution.' },
  { label: 'Threshold Gaming', desc: 'Random offsets on circuit breaker thresholds prevent adversarial threshold probing.' },
  { label: 'Sampling Gaming', desc: 'Verifiable random episode & feed selection eliminates predictable validation patterns.' },
];

// ── Helpers ─────────────────────────────────────────────────────────────

let _entryCounter = 0;

function generateHash(): string {
  const chars = '0123456789abcdef';
  let hash = '0x';
  for (let i = 0; i < 64; i++) hash += chars[Math.floor(Math.random() * chars.length)];
  return hash;
}

function shortHash(hash: string): string {
  return `${hash.substring(0, 6)}...${hash.substring(60)}`;
}

function randomBetween(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function derivedEffectFor(component: VRFComponent): string {
  switch (component) {
    case 'commit-reveal':
      return `Delay: +${Math.floor(randomBetween(30, 60))}s`;
    case 'circuit-breaker':
      return `Threshold offset: +${randomBetween(1.0, 5.0).toFixed(1)}%`;
    case 'data-validation':
      return `Feeds sampled: ${Math.floor(randomBetween(2, 5))}/6`;
    case 'rlmf-sampling':
      return `Episodes: ${Math.floor(randomBetween(64, 256))}`;
    case 'entropy-pricing':
      return `Fee multiplier: ${randomBetween(1.01, 1.25).toFixed(2)}x`;
    case 'oracle-failover':
      return Math.random() > 0.8
        ? `Fallback-${Math.floor(randomBetween(1, 4))}`
        : 'Provider: Primary';
  }
}

function generateAuditEntry(): AuditEntry {
  const component = COMPONENTS[Math.floor(Math.random() * COMPONENTS.length)];
  const hash = generateHash();
  const block = 2847000 + Math.floor(Math.random() * 500);
  const statusRoll = Math.random();
  const status: AuditEntry['status'] =
    statusRoll > 0.99 ? 'failed' : statusRoll > 0.97 ? 'pending' : 'verified';

  return {
    id: `ae-${++_entryCounter}`,
    time: new Date().toISOString().split('T')[1].slice(0, 8),
    component,
    requestId: shortHash(hash),
    blockTx: `BLK #${block.toLocaleString()}`,
    derivedEffect: derivedEffectFor(component),
    status,
  };
}

function getStatusDot(status: string) {
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
}

// ── Component ───────────────────────────────────────────────────────────

export function VRFPage() {
  const auditSectionRef = useRef<HTMLDivElement>(null);

  // State
  const [applicationPoints, setApplicationPoints] = useState<ApplicationPoint[]>(INITIAL_APPLICATION_POINTS);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [auditFilters, setAuditFilters] = useState<AuditFilters>({ component: 'all', status: 'all' });
  const [isLive, setIsLive] = useState(true);
  const [hashCopied, setHashCopied] = useState(false);
  const [drawerEntry, setDrawerEntry] = useState<AuditDrawerData | null>(null);

  // LMSR cost (static demo)
  const lmsrDemoCost = lmsrCost(0.52, 0.57, LIQUIDITY_B);
  const deltaQ = Math.abs(Math.log(0.57 / (1 - 0.57)) - Math.log(0.52 / (1 - 0.52)));

  // ── Generators ──────────────────────────────────────────────────────

  const addAuditEntry = useCallback(() => {
    setAuditTrail(prev => [generateAuditEntry(), ...prev.slice(0, 49)]);
  }, []);

  const updateRandomApplicationPoint = useCallback(() => {
    setApplicationPoints(prev => {
      const idx = Math.floor(Math.random() * prev.length);
      const updated = [...prev];
      const point = updated[idx];
      updated[idx] = {
        ...point,
        lastDraw: {
          timestamp: new Date().toISOString().split('T')[1].slice(0, 8) + ' UTC',
          requestId: shortHash(generateHash()),
        },
        result: derivedEffectFor(point.id),
      };
      return updated;
    });
  }, []);

  const refreshDashboard = useCallback(() => {
    addAuditEntry();
    updateRandomApplicationPoint();
  }, [addAuditEntry, updateRandomApplicationPoint]);

  // ── TopActionBar ────────────────────────────────────────────────────

  useRegisterTopActionBarActions({
    onLive: () => setIsLive(prev => !prev),
    onRefresh: refreshDashboard,
  });

  // ── Effects ─────────────────────────────────────────────────────────

  useEffect(() => {
    const initial = Array.from({ length: 10 }, () => generateAuditEntry());
    setAuditTrail(initial);
  }, []);

  useEffect(() => {
    if (!isLive) return;
    const auditInterval = setInterval(addAuditEntry, 3000);
    const pointInterval = setInterval(updateRandomApplicationPoint, 10000);
    return () => {
      clearInterval(auditInterval);
      clearInterval(pointInterval);
    };
  }, [isLive, addAuditEntry, updateRandomApplicationPoint]);

  // Close drawer on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerEntry(null);
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // ── Filtered audit trail ────────────────────────────────────────────

  const filteredAuditTrail = useMemo(() => {
    return auditTrail.filter(entry => {
      if (auditFilters.component !== 'all' && entry.component !== auditFilters.component) return false;
      if (auditFilters.status !== 'all' && entry.status !== auditFilters.status) return false;
      return true;
    });
  }, [auditTrail, auditFilters]);

  // ── Handlers ────────────────────────────────────────────────────────

  const handleCopyHash = useCallback(() => {
    navigator.clipboard.writeText(COMMITMENT_HASH);
    setHashCopied(true);
    setTimeout(() => setHashCopied(false), 2000);
  }, []);

  const openAuditDrawer = useCallback((point: ApplicationPoint) => {
    const fullHash = generateHash();
    setDrawerEntry({
      component: point.id,
      name: point.name,
      description: point.description,
      icon: point.icon,
      requestId: fullHash,
      shortRequestId: shortHash(fullHash),
      blockTx: `BLK #${(2847000 + Math.floor(Math.random() * 500)).toLocaleString()}`,
      seed: generateHash(),
      proofStatus: Math.random() > 0.05 ? 'verified' : 'pending',
      derivedEffect: point.result,
      timestamp: point.lastDraw.timestamp,
    });
    // Also filter audit trail to this component
    setAuditFilters({ component: point.id, status: 'all' });
    setTimeout(() => {
      auditSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  }, []);

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">

      {/* ═══════════ Section 1: Entropy Commitments ═══════════ */}

      <div className="flex items-center gap-2 mb-1">
        <Shield className="w-4 h-4 text-status-vrf" />
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          Entropy Commitments
        </h2>
        <span className="chip chip-info text-[10px]">Simulated</span>
      </div>

      {/* Commitment Hash pill */}
      <div className="flex items-center gap-2 bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2">
        <span className="text-[10px] text-terminal-text-muted uppercase tracking-wider font-semibold">
          Commitment root
        </span>
        <span
          className="font-mono text-status-vrf text-xs"
          title="Simulated feed"
        >
          {shortHash(COMMITMENT_HASH)}
        </span>
        <button
          onClick={handleCopyHash}
          className="p-0.5 rounded text-terminal-text-muted hover:text-terminal-text transition-colors"
          title="Copy full hash"
        >
          <Copy className="w-3 h-3" />
        </button>
        {hashCopied && (
          <span className="text-[10px] text-status-success font-semibold animate-fade-in">
            Copied
          </span>
        )}
        <span className="chip chip-info text-[9px] ml-auto">Simulated</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* VRF Provider */}
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            VRF Provider
          </div>
          <div className="text-lg font-mono font-bold text-terminal-text">Chainlink VRF v2</div>
          <div className="text-xs text-terminal-text-muted mt-1">Base Mainnet</div>
          <div className="flex items-center gap-2 mt-2">
            <div className="w-5 h-5 rounded bg-[#375bd2] text-white flex items-center justify-center font-bold text-[9px]">CL</div>
            <span className="chip chip-info text-[9px]">Simulated</span>
          </div>
        </div>

        {/* Verification Rate */}
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            Verification Rate
          </div>
          <div className="text-2xl font-mono font-bold text-status-success">99.97%</div>
          <div className="text-xs text-terminal-text-muted mt-1">Proof validated</div>
        </div>

        {/* Median Fulfilment */}
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            Median Fulfilment
          </div>
          <div className="text-2xl font-mono font-bold text-terminal-text">2.3s</div>
          <div className="text-xs text-terminal-text-muted mt-1">Block to fulfilment</div>
        </div>

        {/* VRF Events (24h) */}
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            VRF Events (24h)
          </div>
          <div className="text-2xl font-mono font-bold text-terminal-text">847</div>
          <div className="text-xs text-terminal-text-muted mt-1">Fulfilments across all components</div>
        </div>

        {/* Coordinator Uptime */}
        <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
          <div className="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
            Coordinator Uptime
          </div>
          <div className="text-2xl font-mono font-bold text-status-success">99.99%</div>
          <div className="text-xs text-terminal-text-muted mt-1">30-day SLO</div>
        </div>
      </div>

      {/* ═══════════ Section 2: Where VRF Is Applied ═══════════ */}

      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-status-vrf" />
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          Where VRF Is Applied
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {applicationPoints.map(point => {
          const Icon = point.icon;
          return (
            <div key={point.id} className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
              {/* Card header */}
              <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex items-center gap-2">
                <Icon className="w-4 h-4 text-status-vrf" />
                <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
                  {point.name}
                </span>
              </div>

              <div className="p-4 space-y-3">
                {/* Description */}
                <p className="text-xs text-terminal-text-secondary leading-relaxed">
                  {point.description}
                </p>

                {/* Last draw info */}
                <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-terminal-text-muted">Last draw</span>
                    <span className="font-mono text-terminal-text-secondary">{point.lastDraw.timestamp}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-terminal-text-muted">Request ID</span>
                    <span className="font-mono text-status-vrf" title="Simulated feed">{point.lastDraw.requestId}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-terminal-text-muted">Result</span>
                    <span className="font-mono font-semibold text-terminal-text">{point.result}</span>
                  </div>
                </div>

                {/* Audit details button → opens drawer */}
                <button
                  onClick={() => openAuditDrawer(point)}
                  className="w-full text-xs text-status-vrf hover:text-status-vrf/80 transition-colors flex items-center justify-center gap-1 py-1.5 rounded-lg border border-status-vrf/20 hover:border-status-vrf/40 bg-status-vrf/5"
                >
                  <Search className="w-3 h-3" />
                  Audit details
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* ═══════════ Section 3: LMSR Integrity Coupling ═══════════ */}

      <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex items-center gap-2">
          <Lock className="w-4 h-4 text-status-entropy" />
          <span className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
            LMSR Integrity Coupling
          </span>
          <span className="chip chip-info text-[10px]">CFPM</span>
        </div>

        <div className="p-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Left column — Anti-Manipulation Surfaces */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">
                Anti-Manipulation Surfaces
              </h3>

              {ANTI_MANIPULATION_SURFACES.map(surface => (
                <div key={surface.label} className="flex gap-3 items-start">
                  <div className="w-1.5 h-1.5 rounded-full bg-status-vrf mt-1.5 flex-shrink-0" />
                  <div>
                    <div className="text-xs font-medium text-terminal-text">{surface.label}</div>
                    <div className="text-xs text-terminal-text-secondary mt-0.5">{surface.desc}</div>
                  </div>
                </div>
              ))}

              <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 mt-2">
                <p className="text-xs text-terminal-text-muted italic leading-relaxed">
                  No order book &rarr; no queue games; VRF protects adversarial fairness in discrete events (sabotage, thresholds, sampling).
                </p>
              </div>
            </div>

            {/* Right column — Cost to Move (LMSR Demo) */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-terminal-text-secondary uppercase tracking-wider">
                Cost to Move (LMSR Demo)
              </h3>

              <div className="bg-terminal-bg border border-terminal-border rounded-lg p-4 space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="data-label">From</span>
                  <span className="font-mono text-terminal-text">YES 52.0%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">To</span>
                  <span className="font-mono text-terminal-text">YES 57.0%</span>
                </div>

                {/* Δq breakdown line */}
                <div className="flex items-center gap-3 text-[11px] text-terminal-text-muted font-mono py-1">
                  <span>&Delta;p: <span className="text-echelon-cyan">+5.0%</span></span>
                  <span className="text-terminal-border">|</span>
                  <span>&Delta;q: <span className="text-terminal-text">{deltaQ.toFixed(3)}</span> shares</span>
                  <span className="text-terminal-border">|</span>
                  <span>Cost: <span className="text-status-entropy font-semibold">${lmsrDemoCost.toFixed(2)}</span></span>
                </div>

                <div className="border-t border-terminal-border border-dashed pt-3 space-y-2">
                  <div className="flex justify-between items-baseline">
                    <span className="data-label">Cost</span>
                    <span className="font-mono font-bold text-status-entropy text-sm">
                      ${lmsrDemoCost.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="data-label">Liquidity (b)</span>
                    <span className="font-mono text-terminal-text-secondary">{LIQUIDITY_B}</span>
                  </div>
                </div>
              </div>

              <div className="bg-terminal-bg border border-status-vrf/20 rounded-lg p-3">
                <p className="text-xs text-terminal-text-muted leading-relaxed">
                  <span className="text-status-vrf font-semibold">Note:</span> VRF does not set prices;
                  it protects event fairness &amp; sampling. The LMSR cost function is deterministic
                  given current state.
                </p>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* ═══════════ Status Strip ═══════════ */}

      <div className="flex items-center gap-2 px-4 py-2 bg-terminal-panel border border-terminal-border rounded-lg">
        <span className="w-1.5 h-1.5 rounded-full bg-status-success shadow-[0_0_4px_rgba(74,222,128,0.4)]" />
        <span className="text-xs font-semibold text-status-success">All systems nominal</span>
        <span className="text-xs text-terminal-text-muted ml-auto font-mono">
          VRF: 2.3s &middot; Oracle: Mode 0 &middot; Circuit breakers: standby
        </span>
      </div>

      {/* ═══════════ Section 4: Audit Trail ═══════════ */}

      <div ref={auditSectionRef} className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        {/* Header with filters */}
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-terminal-text-muted" />
            <span className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
              Audit Trail
            </span>
            <span className="text-xs text-terminal-text-muted font-mono">
              ({filteredAuditTrail.length})
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Component filter */}
            <select
              value={auditFilters.component}
              onChange={e => setAuditFilters(prev => ({ ...prev, component: e.target.value as VRFComponent | 'all' }))}
              className="bg-terminal-bg border border-terminal-border rounded-lg px-2 py-1.5 text-xs text-terminal-text-secondary focus:outline-none focus:border-status-vrf/50 cursor-pointer"
            >
              <option value="all">All Components</option>
              {COMPONENTS.map(c => (
                <option key={c} value={c}>{COMPONENT_LABELS[c]}</option>
              ))}
            </select>

            {/* Status filter */}
            <select
              value={auditFilters.status}
              onChange={e => setAuditFilters(prev => ({ ...prev, status: e.target.value as AuditEntry['status'] | 'all' }))}
              className="bg-terminal-bg border border-terminal-border rounded-lg px-2 py-1.5 text-xs text-terminal-text-secondary focus:outline-none focus:border-status-vrf/50 cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="verified">Verified</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>

            {/* Clear filters */}
            {(auditFilters.component !== 'all' || auditFilters.status !== 'all') && (
              <button
                onClick={() => setAuditFilters({ component: 'all', status: 'all' })}
                className="text-xs text-terminal-text-muted hover:text-terminal-text transition-colors flex items-center gap-1"
              >
                <X className="w-3 h-3" />
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-terminal-border bg-terminal-bg sticky top-0 z-10">
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Time</th>
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Component</th>
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Request ID</th>
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Block / Tx</th>
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Derived Effect</th>
                <th className="text-left px-4 py-2 font-semibold text-terminal-text-muted uppercase tracking-wider text-[10px]">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredAuditTrail.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-xs text-terminal-text-muted">
                    No entries match the current filters.
                  </td>
                </tr>
              ) : (
                filteredAuditTrail.map(entry => (
                  <tr key={entry.id} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-terminal-text-muted">{entry.time}</td>
                    <td className="px-4 py-2.5 text-terminal-text-secondary">{COMPONENT_LABELS[entry.component]}</td>
                    <td className="px-4 py-2.5 font-mono text-status-vrf" title="Simulated feed">{entry.requestId}</td>
                    <td className="px-4 py-2.5 font-mono text-terminal-text-muted" title="Simulated feed">{entry.blockTx}</td>
                    <td className="px-4 py-2.5 font-mono text-terminal-text">{entry.derivedEffect}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        {getStatusDot(entry.status)}
                        <span className="capitalize text-terminal-text-secondary">{entry.status}</span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ═══════════ Audit Detail Drawer ═══════════ */}

      {drawerEntry && (
        <div
          className="fixed inset-0 z-[300] bg-black/50"
          onClick={() => setDrawerEntry(null)}
        />
      )}
      {drawerEntry && (() => {
        const DrawerIcon = drawerEntry.icon;
        return (
          <div
            className="fixed top-[60px] right-6 w-[420px] max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-[310] shadow-elevation-3 bg-terminal-overlay border border-terminal-border"
            onClick={e => e.stopPropagation()}
          >
            {/* Drawer header */}
            <div className="section-header">
              <div className="flex items-center gap-2">
                <DrawerIcon className="w-4 h-4 text-status-vrf" />
                <span className="section-title-accented">{drawerEntry.name}</span>
              </div>
              <button
                onClick={() => setDrawerEntry(null)}
                className="p-1 rounded transition-colors text-terminal-text-muted hover:text-terminal-text"
              >
                &#x2715;
              </button>
            </div>

            {/* Drawer body */}
            <div className="p-4 overflow-y-auto space-y-4">
              <p className="text-xs text-terminal-text-secondary leading-relaxed">
                {drawerEntry.description}
              </p>

              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="data-label">Request ID</span>
                  <span className="font-mono text-status-vrf text-[11px] break-all text-right max-w-[260px]" title="Simulated feed">
                    {drawerEntry.requestId}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">Block / Tx</span>
                  <span className="font-mono text-terminal-text-secondary" title="Simulated feed">{drawerEntry.blockTx}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">VRF Seed</span>
                  <span className="font-mono text-terminal-text-muted text-[11px] break-all text-right max-w-[260px]" title="Simulated feed">
                    {shortHash(drawerEntry.seed)}
                  </span>
                </div>
                <div className="flex justify-between text-xs items-center">
                  <span className="data-label">Proof Status</span>
                  <div className="flex items-center gap-1.5">
                    {getStatusDot(drawerEntry.proofStatus)}
                    <span className="capitalize text-terminal-text-secondary">{drawerEntry.proofStatus}</span>
                  </div>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">Derived Effect</span>
                  <span className="font-mono font-semibold text-terminal-text">{drawerEntry.derivedEffect}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">Component</span>
                  <span className="text-terminal-text-secondary">{COMPONENT_LABELS[drawerEntry.component]}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="data-label">Timestamp</span>
                  <span className="font-mono text-terminal-text-muted">{drawerEntry.timestamp}</span>
                </div>
              </div>

              <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3 mt-2">
                <p className="text-[10px] text-terminal-text-muted italic">
                  All values are from a simulated feed. On-chain verification will be available when Chainlink VRF is integrated on Base Mainnet.
                </p>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
