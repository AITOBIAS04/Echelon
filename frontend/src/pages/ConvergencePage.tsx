/**
 * ConvergencePage — Thin route wrapper for convergence heatmap.
 */

import { ConvergenceMap } from '../components/convergence/ConvergenceMap';

export function ConvergencePage() {
  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-5xl mx-auto">
        <ConvergenceMap />
      </div>
    </div>
  );
}
