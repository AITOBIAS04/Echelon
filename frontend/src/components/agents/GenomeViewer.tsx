/**
 * GenomeViewer — Read-only YAML-style display of agent genome traits.
 */

import type { Agent } from '../../types/agents';
import { Dna } from 'lucide-react';

interface GenomeViewerProps {
  agent: Agent;
}

function renderGenomeValue(value: unknown, depth = 0): string {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    return value.map((v) => `${' '.repeat((depth + 1) * 2)}- ${renderGenomeValue(v, depth + 1)}`).join('\n');
  }
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => {
        const rendered = renderGenomeValue(v, depth + 1);
        if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
          return `${' '.repeat((depth + 1) * 2)}${k}:\n${rendered}`;
        }
        return `${' '.repeat((depth + 1) * 2)}${k}: ${rendered}`;
      })
      .join('\n');
  }
  return String(value);
}

export function GenomeViewer({ agent }: GenomeViewerProps) {
  const genomeEntries = Object.entries(agent.genome);

  if (genomeEntries.length === 0) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 text-center">
        <Dna className="w-6 h-6 text-terminal-text-muted mx-auto mb-2" />
        <div className="text-xs text-terminal-text-muted">No genome data available.</div>
      </div>
    );
  }

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Dna className="w-4 h-4 text-echelon-cyan" />
        <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wider">
          Genome
        </h3>
      </div>

      <div className="bg-terminal-panel rounded-lg p-3 font-mono text-xs overflow-x-auto">
        <pre className="text-terminal-text whitespace-pre-wrap">
          {genomeEntries
            .map(([key, value]) => {
              const rendered = renderGenomeValue(value, 0);
              if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                return `${key}:\n${rendered}`;
              }
              return `${key}: ${rendered}`;
            })
            .join('\n')}
        </pre>
      </div>

      <div className="mt-2 text-[10px] text-terminal-text-muted">
        {agent.parent_agent_ids.length > 0
          ? `Lineage: ${agent.parent_agent_ids.join(' × ')}`
          : 'Genesis agent — no parent lineage'}
      </div>
    </div>
  );
}
