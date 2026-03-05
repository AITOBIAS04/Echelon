/**
 * ConvergenceMap — 2D grid heatmap of OSINT signal convergence.
 * Grey → amber → red based on signal density per 1° × 1° cell.
 * Click cell to expand event types, sources, matched theatres.
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { ConvergenceCell } from './ConvergenceCell';
import type { CellData } from './ConvergenceCell';
import { MapPin, X } from 'lucide-react';

interface ConvergenceResponse {
  cells: Array<{
    lat: number;
    lon: number;
    density: number;
    events: number;
    sources: string[];
    theatres: string[];
  }>;
  grid_size: number;
}

function useConvergenceData() {
  return useQuery({
    queryKey: ['convergence', 'map'],
    queryFn: async (): Promise<CellData[]> => {
      const { data } = await apiClient.get<ConvergenceResponse>('/api/v1/convergence/heatmap');
      return data.cells.map((c) => ({
        lat: c.lat,
        lon: c.lon,
        density: c.density,
        events: c.events,
        sources: c.sources,
        theatres: c.theatres,
      }));
    },
    refetchInterval: 60_000,
  });
}

// Generate grid from cell data — 12×8 grid (covering key regions)
const GRID_COLS = 12;
const GRID_ROWS = 8;

function buildGrid(cells: CellData[]): CellData[][] {
  // Create empty grid
  const grid: CellData[][] = Array.from({ length: GRID_ROWS }, (_, r) =>
    Array.from({ length: GRID_COLS }, (_, c) => ({
      lat: 60 - r * 15, // 60°N to -45°S
      lon: -180 + c * 30, // -180 to 150
      density: 0,
      events: 0,
      sources: [],
      theatres: [],
    })),
  );

  // Map API cells onto grid
  for (const cell of cells) {
    const r = Math.max(0, Math.min(GRID_ROWS - 1, Math.floor((60 - cell.lat) / 15)));
    const c = Math.max(0, Math.min(GRID_COLS - 1, Math.floor((cell.lon + 180) / 30)));
    grid[r][c] = cell;
  }

  return grid;
}

export function ConvergenceMap() {
  const { data: cells, isLoading, error } = useConvergenceData();
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  const grid = useMemo(() => buildGrid(cells ?? []), [cells]);
  const maxDensity = useMemo(
    () => (cells ?? []).reduce((max, c) => Math.max(max, c.density), 0),
    [cells],
  );

  if (error) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6">
        <div className="text-xs text-red-400">Failed to load convergence data.</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
            Convergence Map
          </h2>
          <p className="text-xs text-terminal-text-muted mt-1">
            OSINT signal density by region. Click a cell for detail.
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-terminal-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-zinc-500/30" /> Low
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-amber-500/25" /> Med
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-amber-500/50" /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-red-500/60" /> Critical
          </span>
        </div>
      </div>

      {/* Grid */}
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
        {isLoading ? (
          <div className="text-xs text-terminal-text-muted text-center py-12">
            Loading convergence data...
          </div>
        ) : (
          <div
            className="grid gap-1"
            style={{ gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)` }}
          >
            {grid.flat().map((cell, i) => (
              <ConvergenceCell
                key={i}
                cell={cell}
                maxDensity={maxDensity}
                isSelected={selectedCell?.lat === cell.lat && selectedCell?.lon === cell.lon}
                onClick={() => setSelectedCell(cell)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selectedCell && (
        <div className="bg-terminal-surface border border-echelon-cyan/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-echelon-cyan" />
              <span className="text-sm font-mono text-terminal-text">
                {selectedCell.lat}°, {selectedCell.lon}°
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedCell(null)}
              className="p-1 text-terminal-text-muted hover:text-terminal-text"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-terminal-text-muted block mb-1">Events</span>
              <span className="text-terminal-text font-mono text-lg">{selectedCell.events}</span>
            </div>
            <div>
              <span className="text-terminal-text-muted block mb-1">Sources</span>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {selectedCell.sources.length > 0 ? (
                  selectedCell.sources.map((s) => (
                    <span
                      key={s}
                      className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-echelon-cyan/10 text-echelon-cyan"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-terminal-text-muted">—</span>
                )}
              </div>
            </div>
            <div>
              <span className="text-terminal-text-muted block mb-1">Matched Theatres</span>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {selectedCell.theatres.length > 0 ? (
                  selectedCell.theatres.map((t) => (
                    <span
                      key={t}
                      className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400"
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span className="text-terminal-text-muted">—</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
