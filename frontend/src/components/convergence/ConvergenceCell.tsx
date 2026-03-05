/**
 * ConvergenceCell — Single cell in the convergence heatmap grid.
 * Colour: grey → amber → red based on signal density.
 */

import { clsx } from 'clsx';

export interface CellData {
  lat: number;
  lon: number;
  density: number; // 0-1 normalised
  events: number;
  sources: string[];
  theatres: string[];
}

interface ConvergenceCellProps {
  cell: CellData;
  maxDensity: number;
  isSelected: boolean;
  onClick: () => void;
}

function getCellColor(density: number, max: number): string {
  if (max === 0) return 'bg-zinc-800/40';
  const ratio = density / max;
  if (ratio >= 0.7) return 'bg-red-500/60';
  if (ratio >= 0.4) return 'bg-amber-500/50';
  if (ratio >= 0.15) return 'bg-amber-500/25';
  if (ratio > 0) return 'bg-zinc-500/30';
  return 'bg-zinc-800/40';
}

export function ConvergenceCell({ cell, maxDensity, isSelected, onClick }: ConvergenceCellProps) {
  const color = getCellColor(cell.density, maxDensity);

  return (
    <button
      type="button"
      onClick={onClick}
      title={`${cell.lat}°, ${cell.lon}° — ${cell.events} events`}
      className={clsx(
        'w-full aspect-square rounded-sm transition-all duration-200 border',
        color,
        isSelected
          ? 'border-echelon-cyan ring-1 ring-echelon-cyan/40'
          : 'border-transparent hover:border-terminal-border',
      )}
    />
  );
}
