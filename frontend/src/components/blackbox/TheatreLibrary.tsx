import { useState, useEffect } from 'react';
import { FileText, ChevronRight, ChevronDown, AlertTriangle, Zap, Target, FolderOpen } from 'lucide-react';
import { clsx } from 'clsx';

interface TheatreMeta {
  name: string;
  id: string;
  type: string;
  episodeLengthSec: number;
  forkPointsPerRunRange: [number, number];
  settlementLatencySec: number;
}

interface ObjectiveComponent {
  component: string;
  weight: number;
  description: string;
}

interface ForkPoint {
  trigger: string;
  marketQuestion: string;
  options: string[];
  decisionWindowSec: number;
}

interface SaboteurCard {
  card: string;
  price: number;
  boundedEffect: number;
  notes: string;
}

interface TelemetrySpec {
  snapshotHz: number;
  estimatedSnapshotsPerEpisode: number;
  keyStateVectors: string[];
}

interface SettlementRules {
  oracle: string;
  success: {
    condition: string;
    payoutMultiplier: number;
  };
  failure: {
    condition: string;
    payoutMultiplier: number;
  };
  paradoxRule: {
    trigger: string;
    resolution: string;
  };
}

interface Theatre {
  meta: TheatreMeta;
  objectiveVector: ObjectiveComponent[];
  telemetrySpec: TelemetrySpec;
  forkPointSchema: ForkPoint[];
  saboteurDeck: SaboteurCard[];
  settlementRules: SettlementRules;
}

const THEATRE_FILES = [
  'NEON_COURIER_V1.json',
  'DISASTER_RESPONSE_V1.json',
  'ORBITAL_SALVAGE_V1.json',
  'BLACKSITE_HEIST_V1.json',
];

export function TheatreLibrary() {
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [selectedTheatre, setSelectedTheatre] = useState<Theatre | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['meta']));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTheatres = async () => {
      try {
        setLoading(true);
        const loadedTheatres: Theatre[] = [];

        for (const file of THEATRE_FILES) {
          try {
            const response = await fetch(`/theatres/${file}`);
            if (!response.ok) {
              throw new Error(`Failed to load ${file}: ${response.statusText}`);
            }
            const data: Theatre = await response.json();
            loadedTheatres.push(data);
          } catch (err) {
            console.error(`Error loading ${file}:`, err);
          }
        }

        setTheatres(loadedTheatres);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load theatres');
      } finally {
        setLoading(false);
      }
    };

    loadTheatres();
  }, []);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const getTypeColor = (type: string): string => {
    switch (type) {
      case 'courier':
        return 'text-blue-400';
      case 'crisis_management':
        return 'text-amber-400';
      case 'space_operations':
        return 'text-purple-400';
      case 'covert_operations':
        return 'text-red-400';
      default:
        return 'text-emerald-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-blue-400 animate-pulse" />
          <span className="text-slate-400">Loading theatres...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <AlertTriangle className="w-12 h-12 mb-4 text-red-400 opacity-50" />
        <p className="text-lg font-medium mb-2 text-slate-200">Error loading theatres</p>
        <p className="text-sm text-slate-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      {/* Left: Theatre List */}
      <div className="w-64 flex-shrink-0 bg-slate-900/50 border border-slate-700/50 rounded-lg p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-4 flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-blue-400" />
          Theatres ({theatres.length})
        </h3>
        <div className="space-y-2">
          {theatres.map((theatre) => {
            const isSelected = selectedTheatre?.meta.id === theatre.meta.id;
            const typeColor = getTypeColor(theatre.meta.type);

            return (
              <button
                key={theatre.meta.id}
                onClick={() => {
                  setSelectedTheatre(theatre);
                  setExpandedSections(new Set(['meta']));
                }}
                className={clsx(
                  'w-full text-left p-3 rounded-md border transition-all',
                  isSelected
                    ? 'bg-blue-500/10 border-blue-500/50 text-blue-400'
                    : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-blue-500/30 hover:text-slate-200'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={clsx(
                      'w-2 h-2 rounded-full',
                      isSelected ? 'bg-blue-400' : 'bg-current opacity-50'
                    )}
                    style={{ color: isSelected ? undefined : typeColor }}
                  />
                  <span className="font-medium text-sm">{theatre.meta.name}</span>
                </div>
                <div className="text-xs text-slate-500 font-mono">{theatre.meta.id}</div>
                <div className="text-xs text-slate-500 mt-1 capitalize">{theatre.meta.type.replace('_', ' ')}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: Theatre Detail */}
      <div className="flex-1 bg-slate-900/50 border border-slate-700/50 rounded-lg p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {!selectedTheatre ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <FileText className="w-16 h-16 mb-4 text-slate-500 opacity-30" />
            <p className="text-lg font-medium">Select a theatre to view details</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Meta Section */}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('meta')}
                className="w-full flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-800 transition"
              >
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-400" />
                  Meta
                </h3>
                {expandedSections.has('meta') ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
              </button>
              {expandedSections.has('meta') && (
                <div className="p-4 space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-500 text-xs">Name</span>
                      <div className="text-slate-200 font-medium">{selectedTheatre.meta.name}</div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">ID</span>
                      <div className="font-mono text-slate-400 text-xs">{selectedTheatre.meta.id}</div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">Type</span>
                      <div className="capitalize text-slate-200">{selectedTheatre.meta.type.replace('_', ' ')}</div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">Episode Length</span>
                      <div className="text-slate-200">{selectedTheatre.meta.episodeLengthSec}s</div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">Fork Points</span>
                      <div className="text-slate-200">
                        {selectedTheatre.meta.forkPointsPerRunRange[0]}-{selectedTheatre.meta.forkPointsPerRunRange[1]}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">Settlement Latency</span>
                      <div className="text-slate-200">{selectedTheatre.meta.settlementLatencySec}s</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Fork Point Schema */}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('forkPointSchema')}
                className="w-full flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-800 transition"
              >
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  Fork Point Schema ({selectedTheatre.forkPointSchema.length})
                </h3>
                {expandedSections.has('forkPointSchema') ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
              </button>
              {expandedSections.has('forkPointSchema') && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700/50">
                        <th className="text-left p-3 text-slate-500 uppercase">Trigger</th>
                        <th className="text-left p-3 text-slate-500 uppercase">Market Question</th>
                        <th className="text-left p-3 text-slate-500 uppercase">Options</th>
                        <th className="text-left p-3 text-slate-500 uppercase">Decision Window</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTheatre.forkPointSchema.map((fork, index) => (
                        <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                          <td className="p-3 font-mono text-blue-400">{fork.trigger}</td>
                          <td className="p-3 text-slate-400">{fork.marketQuestion}</td>
                          <td className="p-3">
                            <div className="flex flex-wrap gap-1">
                              {fork.options.map((opt, optIdx) => (
                                <span
                                  key={optIdx}
                                  className="px-2 py-0.5 bg-slate-800/50 border border-slate-700/50 rounded text-slate-400"
                                >
                                  {opt}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="p-3 text-slate-400">{fork.decisionWindowSec}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Saboteur Deck */}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('saboteurDeck')}
                className="w-full flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-800 transition"
              >
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  Saboteur Deck ({selectedTheatre.saboteurDeck.length})
                </h3>
                {expandedSections.has('saboteurDeck') ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
              </button>
              {expandedSections.has('saboteurDeck') && (
                <div className="p-4 space-y-2">
                  {selectedTheatre.saboteurDeck.map((card, index) => (
                    <div
                      key={index}
                      className="bg-slate-800/50 border border-slate-700/50 rounded-md p-3"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-slate-200">{card.card}</span>
                        <span className="text-red-400 font-mono">${card.price.toLocaleString()}</span>
                      </div>
                      <div className="text-xs text-slate-500 mb-1">
                        Effect: <span className="text-red-400">{card.boundedEffect < 0 ? '' : '+'}{card.boundedEffect}</span>
                      </div>
                      <div className="text-xs text-slate-400">{card.notes}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Telemetry Spec */}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('telemetrySpec')}
                className="w-full flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-800 transition"
              >
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-emerald-400" />
                  Telemetry Spec
                </h3>
                {expandedSections.has('telemetrySpec') ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
              </button>
              {expandedSections.has('telemetrySpec') && (
                <div className="p-4 space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-500 text-xs">Snapshot Hz</span>
                      <div className="text-slate-200">{selectedTheatre.telemetrySpec.snapshotHz}</div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">Estimated Snapshots</span>
                      <div className="text-slate-200">{selectedTheatre.telemetrySpec.estimatedSnapshotsPerEpisode}</div>
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-xs block mb-2">Key State Vectors</span>
                    <div className="flex flex-wrap gap-2">
                      {selectedTheatre.telemetrySpec.keyStateVectors.map((vector, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded text-xs font-mono text-slate-400"
                        >
                          {vector}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Settlement Rules */}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('settlementRules')}
                className="w-full flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-800 transition"
              >
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-400" />
                  Settlement Rules
                </h3>
                {expandedSections.has('settlementRules') ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
              </button>
              {expandedSections.has('settlementRules') && (
                <div className="p-4 space-y-3 text-sm">
                  <div>
                    <span className="text-slate-500 text-xs">Oracle</span>
                    <div className="font-mono text-blue-400">{selectedTheatre.settlementRules.oracle}</div>
                  </div>
                  <div className="bg-slate-800/50 border border-emerald-500/30 rounded-md p-3">
                    <div className="text-emerald-400 font-medium mb-2">Success Condition</div>
                    <div className="text-slate-400 font-mono text-xs mb-1">
                      {selectedTheatre.settlementRules.success.condition}
                    </div>
                    <div className="text-slate-500 text-xs">
                      Payout Multiplier: <span className="text-emerald-400">{selectedTheatre.settlementRules.success.payoutMultiplier}</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 border border-red-500/30 rounded-md p-3">
                    <div className="text-red-400 font-medium mb-2">Failure Condition</div>
                    <div className="text-slate-400 font-mono text-xs mb-1">
                      {selectedTheatre.settlementRules.failure.condition}
                    </div>
                    <div className="text-slate-500 text-xs">
                      Payout Multiplier: <span className="text-red-400">{selectedTheatre.settlementRules.failure.payoutMultiplier}</span>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 border border-amber-500/30 rounded-md p-3">
                    <div className="text-amber-400 font-medium mb-2">Paradox Rule</div>
                    <div className="text-slate-400 font-mono text-xs mb-1">
                      Trigger: {selectedTheatre.settlementRules.paradoxRule.trigger}
                    </div>
                    <div className="text-slate-400 text-xs">
                      Resolution: {selectedTheatre.settlementRules.paradoxRule.resolution}
                    </div>
</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TheatreLibrary;
