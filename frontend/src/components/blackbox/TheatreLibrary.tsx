import { useState, useEffect } from 'react';
import { FileText, ChevronRight, ChevronDown, AlertTriangle, Zap, Target } from 'lucide-react';

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
        return '#00D4FF'; // cyan
      case 'crisis_management':
        return '#FF9500'; // amber
      case 'space_operations':
        return '#9932CC'; // purple
      case 'covert_operations':
        return '#FF3B3B'; // red
      default:
        return '#00FF41'; // green
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-[#00FF41] animate-pulse">Loading theatre configurations...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-400">
        <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-lg font-semibold mb-2">Error loading theatres</p>
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      {/* Left: Theatre List */}
      <div className="w-64 flex-shrink-0 bg-[#0a0a0a] border border-[#1a3a1a] rounded p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        <h3 className="text-sm font-semibold text-[#00FF41] uppercase tracking-wide mb-4 flex items-center gap-2">
          <FileText className="w-4 h-4" />
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
                className={`
                  w-full text-left p-3 rounded border transition
                  ${isSelected
                    ? 'bg-[#1a3a1a] border-[#00FF41] text-[#00FF41]'
                    : 'bg-[#0D0D0D] border-[#1a3a1a] text-gray-400 hover:border-[#00FF41]/50 hover:text-[#00FF41]/70'
                  }
                `}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: typeColor }}
                  />
                  <span className="font-semibold text-sm">{theatre.meta.name}</span>
                </div>
                <div className="text-xs text-gray-500 font-mono">{theatre.meta.id}</div>
                <div className="text-xs text-gray-600 mt-1 capitalize">{theatre.meta.type.replace('_', ' ')}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: Theatre Detail */}
      <div className="flex-1 bg-[#0a0a0a] border border-[#1a3a1a] rounded p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {!selectedTheatre ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <FileText className="w-16 h-16 mb-4 opacity-30" />
            <p className="text-lg font-semibold">Select a theatre to view details</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Meta Section */}
            <div className="border border-[#1a3a1a] rounded p-4">
              <button
                onClick={() => toggleSection('meta')}
                className="w-full flex items-center justify-between mb-2 text-[#00FF41] hover:text-[#00FF41]/80 transition"
              >
                <h3 className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Meta
                </h3>
                {expandedSections.has('meta') ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedSections.has('meta') && (
                <div className="space-y-2 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-500">Name:</span>
                      <span className="ml-2 text-[#00FF41]">{selectedTheatre.meta.name}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">ID:</span>
                      <span className="ml-2 font-mono text-gray-400">{selectedTheatre.meta.id}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Type:</span>
                      <span className="ml-2 capitalize text-gray-400">{selectedTheatre.meta.type.replace('_', ' ')}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Episode Length:</span>
                      <span className="ml-2 text-gray-400">{selectedTheatre.meta.episodeLengthSec}s</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Fork Points:</span>
                      <span className="ml-2 text-gray-400">
                        {selectedTheatre.meta.forkPointsPerRunRange[0]}-{selectedTheatre.meta.forkPointsPerRunRange[1]}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Settlement Latency:</span>
                      <span className="ml-2 text-gray-400">{selectedTheatre.meta.settlementLatencySec}s</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Fork Point Schema */}
            <div className="border border-[#1a3a1a] rounded p-4">
              <button
                onClick={() => toggleSection('forkPointSchema')}
                className="w-full flex items-center justify-between mb-2 text-[#00FF41] hover:text-[#00FF41]/80 transition"
              >
                <h3 className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Fork Point Schema ({selectedTheatre.forkPointSchema.length})
                </h3>
                {expandedSections.has('forkPointSchema') ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedSections.has('forkPointSchema') && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#1a3a1a]">
                        <th className="text-left p-2 text-gray-500 uppercase">Trigger</th>
                        <th className="text-left p-2 text-gray-500 uppercase">Market Question</th>
                        <th className="text-left p-2 text-gray-500 uppercase">Options</th>
                        <th className="text-left p-2 text-gray-500 uppercase">Decision Window</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTheatre.forkPointSchema.map((fork, index) => (
                        <tr key={index} className="border-b border-[#1a3a1a]/50 hover:bg-[#1a3a1a]/30">
                          <td className="p-2 font-mono text-[#00FF41]">{fork.trigger}</td>
                          <td className="p-2 text-gray-400">{fork.marketQuestion}</td>
                          <td className="p-2">
                            <div className="flex flex-wrap gap-1">
                              {fork.options.map((opt, optIdx) => (
                                <span
                                  key={optIdx}
                                  className="px-2 py-0.5 bg-[#1a3a1a] rounded text-gray-300"
                                >
                                  {opt}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="p-2 text-gray-400">{fork.decisionWindowSec}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Saboteur Deck */}
            <div className="border border-[#1a3a1a] rounded p-4">
              <button
                onClick={() => toggleSection('saboteurDeck')}
                className="w-full flex items-center justify-between mb-2 text-[#00FF41] hover:text-[#00FF41]/80 transition"
              >
                <h3 className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Saboteur Deck ({selectedTheatre.saboteurDeck.length})
                </h3>
                {expandedSections.has('saboteurDeck') ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedSections.has('saboteurDeck') && (
                <div className="space-y-2">
                  {selectedTheatre.saboteurDeck.map((card, index) => (
                    <div
                      key={index}
                      className="bg-[#0D0D0D] border border-[#1a3a1a] rounded p-3"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-[#00FF41]">{card.card}</span>
                        <span className="text-red-400 font-mono">${card.price.toLocaleString()}</span>
                      </div>
                      <div className="text-xs text-gray-500 mb-1">
                        Effect: <span className="text-red-400">{card.boundedEffect < 0 ? '' : '+'}{card.boundedEffect}</span>
                      </div>
                      <div className="text-xs text-gray-400">{card.notes}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Telemetry Spec */}
            <div className="border border-[#1a3a1a] rounded p-4">
              <button
                onClick={() => toggleSection('telemetrySpec')}
                className="w-full flex items-center justify-between mb-2 text-[#00FF41] hover:text-[#00FF41]/80 transition"
              >
                <h3 className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Telemetry Spec
                </h3>
                {expandedSections.has('telemetrySpec') ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedSections.has('telemetrySpec') && (
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-500">Snapshot Hz:</span>
                      <span className="ml-2 text-gray-400">{selectedTheatre.telemetrySpec.snapshotHz}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Estimated Snapshots:</span>
                      <span className="ml-2 text-gray-400">{selectedTheatre.telemetrySpec.estimatedSnapshotsPerEpisode}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500 mb-2 block">Key State Vectors:</span>
                    <div className="flex flex-wrap gap-2">
                      {selectedTheatre.telemetrySpec.keyStateVectors.map((vector, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-[#1a3a1a] rounded text-xs font-mono text-gray-400"
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
            <div className="border border-[#1a3a1a] rounded p-4">
              <button
                onClick={() => toggleSection('settlementRules')}
                className="w-full flex items-center justify-between mb-2 text-[#00FF41] hover:text-[#00FF41]/80 transition"
              >
                <h3 className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Settlement Rules
                </h3>
                {expandedSections.has('settlementRules') ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedSections.has('settlementRules') && (
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-500">Oracle:</span>
                    <span className="ml-2 font-mono text-[#00FF41]">{selectedTheatre.settlementRules.oracle}</span>
                  </div>
                  <div className="bg-[#0D0D0D] border border-[#1a3a1a] rounded p-3">
                    <div className="text-[#00FF41] font-semibold mb-2">Success Condition</div>
                    <div className="text-gray-400 font-mono text-xs mb-1">
                      {selectedTheatre.settlementRules.success.condition}
                    </div>
                    <div className="text-gray-500 text-xs">
                      Payout Multiplier: <span className="text-[#00FF41]">{selectedTheatre.settlementRules.success.payoutMultiplier}</span>
                    </div>
                  </div>
                  <div className="bg-[#0D0D0D] border border-[#1a3a1a] rounded p-3">
                    <div className="text-red-400 font-semibold mb-2">Failure Condition</div>
                    <div className="text-gray-400 font-mono text-xs mb-1">
                      {selectedTheatre.settlementRules.failure.condition}
                    </div>
                    <div className="text-gray-500 text-xs">
                      Payout Multiplier: <span className="text-red-400">{selectedTheatre.settlementRules.failure.payoutMultiplier}</span>
                    </div>
                  </div>
                  <div className="bg-[#0D0D0D] border border-[#1a3a1a] rounded p-3">
                    <div className="text-amber-400 font-semibold mb-2">Paradox Rule</div>
                    <div className="text-gray-400 font-mono text-xs mb-1">
                      Trigger: {selectedTheatre.settlementRules.paradoxRule.trigger}
                    </div>
                    <div className="text-gray-400 text-xs">
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
