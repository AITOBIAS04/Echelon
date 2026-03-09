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
  start: 'var(--e-purple-500)',
  checkpoint: 'var(--e-orange-500)',
  success: 'var(--e-green-600)',
  failure: 'var(--e-red-600)',
  partial: 'var(--e-orange-600)',
  line: 'var(--e-purple-200)',
} as const;

function getNodeColour(node: EpisodeNode, isFirst: boolean, isLast: boolean): string {
  if (isFirst) return COLOURS.start;
  if (isLast) {
    if ((node.reward ?? 0) > 0) return COLOURS.success;
    if ((node.reward ?? 0) < 0) return COLOURS.failure;
    return COLOURS.partial;
  }
  return COLOURS.checkpoint;
}

function getEdgeColour(reward: number): string {
  if (reward > 0) return COLOURS.success;
  if (reward < 0) return COLOURS.failure;
  return COLOURS.line;
}

export function BranchMap({ nodes }: BranchMapProps) {
  if (nodes.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-[var(--e-border-secondary)] bg-[var(--e-bg-sunken)] px-4 py-6 text-center text-[13px] text-[var(--e-text-muted)]">
        No checkpoint data available.
      </div>
    );
  }

  return (
    <div className="space-y-0" data-testid="branch-map">
      {nodes.map((node, index) => {
        const isFirst = index === 0;
        const isLast = index === nodes.length - 1;
        const nodeColour = getNodeColour(node, isFirst, isLast);
        const edgeColour = getEdgeColour(node.reward ?? 0);

        return (
          <div key={node.checkpoint_id} className="flex gap-4">
            <div className="flex w-5 shrink-0 flex-col items-center">
              <div
                className="mt-1 h-3.5 w-3.5 rounded-full border border-white/60 shadow-[0_0_0_3px_var(--e-bg-card)]"
                style={{ backgroundColor: nodeColour }}
                data-testid={`node-${node.sequence_num}`}
              />
              {!isLast ? (
                <div className="mt-1.5 flex-1" style={{ width: '2px', backgroundColor: edgeColour }} />
              ) : null}
            </div>

            <div className="min-w-0 flex-1 pb-5">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-mono text-[11px] text-[var(--e-text-muted)]">
                  {isFirst ? 'start' : `checkpoint ${node.sequence_num}`}
                </span>
                {node.selected_branch ? (
                  <span className="rounded-full border border-[var(--e-purple-200)] bg-[var(--e-purple-50)] px-2 py-0.5 font-mono text-[10px] font-semibold text-[var(--e-purple-700)]">
                    {node.selected_branch}
                  </span>
                ) : null}
                {node.reward != null ? (
                  <span className="font-mono text-[11px] text-[var(--e-text-secondary)]">
                    reward {node.reward}
                  </span>
                ) : null}
              </div>
              <div className="text-[14px] font-medium leading-6 text-[var(--e-text-primary)]">
                {node.market_question}
              </div>
              <div className="mt-1 text-[12px] leading-5 text-[var(--e-text-secondary)]">
                {node.trigger}
                {node.spawned_theatre_id ? ' · spawned theatre output' : ''}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default BranchMap;
