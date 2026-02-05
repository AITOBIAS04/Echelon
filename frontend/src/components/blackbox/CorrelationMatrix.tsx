import { Info } from 'lucide-react';

// Mock correlation data
const timelines = ['TL_FED_RATE', 'TL_OIL_CRISIS', 'TL_CONTAGION', 'TL_GHOST_TANKER'];
const correlations: Record<string, Record<string, number>> = {
  TL_FED_RATE: { TL_FED_RATE: 1, TL_OIL_CRISIS: 0.65, TL_CONTAGION: 0.12, TL_GHOST_TANKER: 0.45 },
  TL_OIL_CRISIS: { TL_FED_RATE: 0.65, TL_OIL_CRISIS: 1, TL_CONTAGION: 0.08, TL_GHOST_TANKER: 0.82 },
  TL_CONTAGION: { TL_FED_RATE: 0.12, TL_OIL_CRISIS: 0.08, TL_CONTAGION: 1, TL_GHOST_TANKER: 0.15 },
  TL_GHOST_TANKER: { TL_FED_RATE: 0.45, TL_OIL_CRISIS: 0.82, TL_CONTAGION: 0.15, TL_GHOST_TANKER: 1 },
};

function getCorrelationColor(value: number): string {
  if (value >= 0.8) return 'bg-echelon-red';
  if (value >= 0.6) return 'bg-echelon-amber';
  if (value >= 0.4) return 'bg-echelon-blue';
  if (value >= 0.2) return 'bg-echelon-cyan/50';
  return 'bg-terminal-border';
}

export function CorrelationMatrix() {
  return (
    <div className="h-full flex flex-col">
      {/* Info */}
      <div className="flex items-center gap-2 mb-4 p-3 bg-terminal-bg rounded">
        <Info className="w-4 h-4 text-echelon-cyan" />
        <span className="text-xs text-terminal-text-muted">
          Correlation strength determines ripple magnitude when wing flaps exceed divergence threshold.
          High correlation (&gt;0.8) = 80% of stability impact transfers to connected timeline.
        </span>
      </div>

      {/* Matrix */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="p-2 text-xs text-terminal-text-muted"></th>
              {timelines.map((tl) => (
                <th key={tl} className="p-2 text-xs text-terminal-text-muted font-normal">
                  {tl.replace('TL_', '')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timelines.map((row) => (
              <tr key={row}>
                <td className="p-2 text-xs text-terminal-text-muted">{row.replace('TL_', '')}</td>
                {timelines.map((col) => {
                  const value = correlations[row][col];
                  return (
                    <td key={col} className="p-1">
                      <div
                        className={`w-full h-12 rounded flex items-center justify-center ${getCorrelationColor(value)}`}
                        title={`${row} ↔ ${col}: ${value.toFixed(2)}`}
                      >
                        <span className="text-xs font-mono text-white/80">{value.toFixed(2)}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-xs text-terminal-text-muted">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-terminal-border rounded"></span> Weak
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-echelon-cyan/50 rounded"></span> Low
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-echelon-blue rounded"></span> Medium
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-echelon-amber rounded"></span> High
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-echelon-red rounded"></span> Critical
        </span>
      </div>
    </div>
  );
}

