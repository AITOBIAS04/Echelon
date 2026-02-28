import type { BundleFileEntry } from '../../types/execution';
import type { ExecutionPath } from '../../types/signal';

interface EvidenceBundleBuilderProps {
  executionPath: ExecutionPath;
  completedCount: number;
  totalCount: number;
  bundleFiles: BundleFileEntry[];
}

export function EvidenceBundleBuilder({
  executionPath,
  completedCount,
  totalCount,
  bundleFiles,
}: EvidenceBundleBuilderProps) {
  const allDone = completedCount >= totalCount;

  // For PRODUCT: show files progressively as episodes complete
  // committed files always visible, complete files appear as episodes finish
  const visibleFiles = bundleFiles.filter((f) => {
    if (f.status === 'committed') return true;
    if (f.path === 'merkle_root') return completedCount > 0;
    if (executionPath === 'PRODUCT') {
      // Show ground_truth, invocations, scores files based on completed count
      const match = f.path.match(/ep_(\d+)/);
      if (match) {
        const epNum = parseInt(match[1], 10);
        return epNum <= completedCount;
      }
    }
    // MARKET: show files progressively based on phase count
    if (executionPath === 'MARKET') {
      const marketOrder = [
        'commitment_receipt.json',
        'market_state/opening_state.json',
        'market_state/trade_log.json',
        'market_state/closing_state.json',
        'resolution/evidence_submission.json',
        'resolution/settlement_output.json',
      ];
      const idx = marketOrder.indexOf(f.path);
      if (idx >= 0) return idx < completedCount;
    }
    return true;
  });

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-echelon-navy">
        Evidence Bundle
      </h3>
      <div className="rounded-md bg-echelon-data-bg p-4 font-mono text-sm">
        {visibleFiles.map((file, idx) => {
          const isLast = idx === visibleFiles.length - 1;
          const prefix = isLast ? '\u2514\u2500\u2500 ' : '\u251C\u2500\u2500 ';
          const hash =
            file.path === 'merkle_root'
              ? allDone
                ? 'a9f3c7e1...'
                : '[computing...]'
              : file.hash ?? '[building...]';

          return (
            <div
              key={file.path}
              className="animate-fade-slide-up"
              style={{ animationDelay: `${idx * 80}ms` }}
            >
              <span className="text-slate-400">{prefix}</span>
              <span className="text-echelon-data-text">{file.path}</span>
              <span className="ml-2 text-slate-400">{hash}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
