import type { TheatreTemplate } from '../types/inquiry';
import type { Episode, MarketPhase, BundleFileEntry } from '../types/execution';
import { truncateHash } from './hash';

/**
 * Generate the evidence bundle file tree for a given template and its episodes/phases.
 */
export function generateBundleFiles(
  template: TheatreTemplate,
  items: Episode[] | MarketPhase[]
): BundleFileEntry[] {
  if (template.execution_path === 'MARKET') {
    return generateMarketBundle(template);
  }
  return generateProductBundle(template, items as Episode[]);
}

function generateProductBundle(
  template: TheatreTemplate,
  episodes: Episode[]
): BundleFileEntry[] {
  const files: BundleFileEntry[] = [
    {
      path: 'manifest.json',
      hash: truncateHash(template.commitment_hash),
      status: 'committed',
    },
    {
      path: 'template.json',
      hash: truncateHash(template.commitment_hash, 12),
      status: 'committed',
    },
  ];

  for (const ep of episodes) {
    files.push({
      path: `ground_truth/${ep.episode_id}.json`,
      hash: truncateHash(ep.ground_truth_hash),
      status: 'complete',
    });
    files.push({
      path: `invocations/${ep.episode_id}_response.json`,
      hash: truncateHash(ep.invocation_hash),
      status: 'complete',
    });
    files.push({
      path: `scores/${ep.episode_id}_score.json`,
      hash: truncateHash(ep.invocation_hash, 12),
      status: 'complete',
    });
  }

  files.push({
    path: 'merkle_root',
    status: 'building',
  });

  return files;
}

function generateMarketBundle(
  template: TheatreTemplate
): BundleFileEntry[] {
  return [
    {
      path: 'manifest.json',
      hash: truncateHash(template.commitment_hash),
      status: 'committed',
    },
    {
      path: 'template.json',
      hash: truncateHash(template.commitment_hash, 12),
      status: 'committed',
    },
    {
      path: 'commitment_receipt.json',
      status: 'building',
    },
    {
      path: 'market_state/opening_state.json',
      hash: 'a1b2c3d4...',
      status: 'building',
    },
    {
      path: 'market_state/trade_log.json',
      hash: 'c3d4e5f6...',
      status: 'building',
    },
    {
      path: 'market_state/closing_state.json',
      hash: 'e5f6a7b8...',
      status: 'building',
    },
    {
      path: 'resolution/evidence_submission.json',
      status: 'building',
    },
    {
      path: 'resolution/settlement_output.json',
      status: 'building',
    },
    {
      path: 'merkle_root',
      status: 'building',
    },
  ];
}
