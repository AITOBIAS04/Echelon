/**
 * VRF Page — Documentation & Roadmap
 *
 * Informational page explaining VRF's role in the Echelon protocol.
 * No simulated data — purely educational content.
 */

const ROADMAP_ITEMS = [
  {
    phase: 'Phase 1',
    title: 'Core Protocol',
    status: 'completed' as const,
    items: [
      'LMSR/CFPM market engine',
      'Butterfly entropy engine',
      'Paradox detection system',
    ],
  },
  {
    phase: 'Phase 2',
    title: 'VRF Integration Design',
    status: 'in-progress' as const,
    items: [
      'Chainlink VRF v2 coordinator setup on Base',
      'Randomised commit-reveal windows',
      'Circuit breaker threshold jitter',
    ],
  },
  {
    phase: 'Phase 3',
    title: 'Live VRF Deployment',
    status: 'planned' as const,
    items: [
      'On-chain VRF subscription management',
      'RLMF episode sampling via VRF',
      'Oracle failover randomisation',
    ],
  },
];

const VRF_APPLICATIONS = [
  {
    name: 'Commit-Reveal Windows',
    description:
      'Randomised execution windows (30-60s) prevent timing attacks on sabotage actions. Front-running becomes impossible when execution timing is unpredictable.',
  },
  {
    name: 'Circuit Breaker Thresholds',
    description:
      'Random offsets on base thresholds prevent adversarial probing. Attackers cannot predict exactly when a circuit breaker will trigger.',
  },
  {
    name: 'Market Data Validation',
    description:
      'Random feed sampling selection prevents predictable validation gaming across OSINT sources.',
  },
  {
    name: 'RLMF Episode Sampling',
    description:
      'Verifiable random episode selection ensures unbiased training data for reinforcement learning from market feedback.',
  },
  {
    name: 'Risk Fee Jitter',
    description:
      'Randomised risk fee adjustment prevents fee prediction gaming on sabotage pricing.',
  },
  {
    name: 'Oracle Failover',
    description:
      'Randomised failover provider selection prevents oracle targeting attacks in degraded modes.',
  },
];

const STATUS_STYLES = {
  completed: 'bg-emerald-500/20 text-emerald-400',
  'in-progress': 'bg-amber-500/20 text-amber-400',
  planned: 'bg-zinc-500/20 text-zinc-400',
};

export function VRFPage() {
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          VRF Integrity System
        </h2>
        <p className="text-xs text-terminal-text-muted mt-1">
          Chainlink VRF provides verifiable randomness for anti-manipulation protections in the Echelon protocol.
          VRF is not yet integrated on-chain — this page documents the architecture and roadmap.
        </p>
      </div>

      {/* VRF Role Explanation */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl p-4">
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
          Why VRF?
        </h3>
        <div className="space-y-2 text-xs text-terminal-text-secondary leading-relaxed">
          <p>
            The Echelon LMSR/CFPM protocol requires unpredictable randomness for
            fairness guarantees. Standard pseudo-random sources are predictable
            and can be gamed by adversarial agents.
          </p>
          <p>
            Chainlink VRF v2 provides cryptographically verifiable random numbers
            on-chain. Each random value comes with a proof that can be verified
            against the VRF coordinator contract, ensuring the randomness was
            generated fairly.
          </p>
          <p>
            VRF does not set prices — the LMSR cost function is deterministic
            given current state. VRF protects event fairness and sampling
            in discrete events (sabotage, thresholds, episode selection).
          </p>
        </div>
      </div>

      {/* Application Points */}
      <div>
        <h3 className="text-xs font-semibold text-terminal-text uppercase tracking-wider mb-3">
          VRF Application Points (6)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {VRF_APPLICATIONS.map((app) => (
            <div
              key={app.name}
              className="bg-terminal-panel border border-terminal-border rounded-xl p-4"
            >
              <h4 className="text-xs font-semibold text-terminal-text mb-2">
                {app.name}
              </h4>
              <p className="text-xs text-terminal-text-secondary leading-relaxed">
                {app.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Roadmap */}
      <div className="bg-terminal-panel border border-terminal-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-terminal-bg/50 border-b border-terminal-border">
          <span className="text-xs font-semibold text-terminal-text uppercase tracking-wider">
            Implementation Roadmap
          </span>
        </div>
        <div className="p-4 space-y-4">
          {ROADMAP_ITEMS.map((item) => (
            <div key={item.phase} className="flex gap-4">
              <div className="flex-shrink-0 w-20">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${STATUS_STYLES[item.status]}`}
                >
                  {item.status}
                </span>
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-terminal-text">
                  {item.phase}: {item.title}
                </div>
                <ul className="mt-1 space-y-0.5">
                  {item.items.map((bullet) => (
                    <li
                      key={bullet}
                      className="text-xs text-terminal-text-muted flex items-start gap-2"
                    >
                      <span className="text-terminal-text-muted mt-1">-</span>
                      {bullet}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reference Link */}
      <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3">
        <p className="text-[10px] text-terminal-text-muted">
          For detailed VRF architecture, see System Bible VII — VRF Integrity Coupling.
          Chainlink VRF v2 documentation is available at docs.chain.link/vrf.
        </p>
      </div>
    </div>
  );
}
