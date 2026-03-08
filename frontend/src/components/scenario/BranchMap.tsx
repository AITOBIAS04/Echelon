/**
 * BranchMap — Tree visualization of scenario run episode results.
 *
 * Renders checkpoint nodes with colour vocabulary:
 * - Start: purple (#8B5CF6)
 * - Checkpoint: orange (#F59E0B)
 * - Success: green (#10B981)
 * - Failure: red (#EF4444)
 * - Partial: dark orange (#D97706)
 */

interface EpisodeNode {
  checkpoint_id: string;
  sequence_num: number;
  trigger: string;
  market_question: string;
  selected_branch: string | null;
  outcome_type: string | null;
  reward: number | null;
  spawned_theatre_id: string | null;
}

interface BranchMapProps {
  nodes: EpisodeNode[];
}

const COLOURS = {
  start: '#8B5CF6',
  checkpoint: '#F59E0B',
  success: '#10B981',
  failure: '#EF4444',
  partial: '#D97706',
} as const;

function getNodeColour(node: EpisodeNode, isFirst: boolean, isLast: boolean): string {
  if (isFirst) return COLOURS.start;
  if (isLast) {
    if (node.reward != null && node.reward > 0) return COLOURS.success;
    if (node.reward != null && node.reward < 0) return COLOURS.failure;
    return COLOURS.partial;
  }
  return COLOURS.checkpoint;
}

function getEdgeColour(reward: number): string {
  if (reward > 0) return COLOURS.success;
  if (reward < 0) return COLOURS.failure;
  return COLOURS.start;
}

export function BranchMap({ nodes }: BranchMapProps) {
  if (nodes.length === 0) {
    return (
      <div className="text-xs text-terminal-text-muted py-4 text-center">
        No checkpoint data available.
      </div>
    );
  }

  return (
    <div className="space-y-0" data-testid="branch-map">
      {nodes.map((node, idx) => {
        const isFirst = idx === 0;
        const isLast = idx === nodes.length - 1;
        const colour = getNodeColour(node, isFirst, isLast);
        const edgeColour = getEdgeColour(node.reward ?? 0);

        return (
          <div key={node.checkpoint_id} className="flex items-stretch gap-3">
            {/* Node indicator + edge line */}
            <div className="flex flex-col items-center w-4 shrink-0">
              <div
                className="w-3 h-3 rounded-full shrink-0 mt-1"
                style={{ backgroundColor: colour }}
                data-testid={`node-${node.sequence_num}`}
                data-colour={colour}
              />
              {!isLast && (
                <div
                  className="w-0.5 flex-1 min-h-[24px]"
                  style={{ backgroundColor: edgeColour }}
                />
              )}
            </div>

            {/* Content */}
            <div className="pb-3 min-w-0">
              <div className="text-xs font-semibold text-terminal-text">
                {isFirst ? 'Start' : `Checkpoint ${node.sequence_num}`}
              </div>
              <div className="text-[10px] text-terminal-text-muted mt-0.5">
                {node.market_question}
              </div>
              <div className="flex items-center gap-2 mt-1 text-[10px]">
                <span
                  className="font-mono px-1 py-0.5 rounded"
                  style={{ backgroundColor: `${colour}20`, color: colour }}
                >
                  {node.selected_branch ?? '—'}
                </span>
                <span className="text-terminal-text-muted">
                  reward: {node.reward ?? '—'}
                </span>
                {node.spawned_theatre_id && (
                  <span className="text-status-success">spawned theatre</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
