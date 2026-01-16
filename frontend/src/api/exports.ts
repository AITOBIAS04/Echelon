import type {
  ExportJob,
  ExportScope,
  ExportFilter,
  ExportDatasetKind,
  DatasetPreview,
  DatasetSchemaField,
} from '../types/exports';

/**
 * Mock Export Jobs Data
 * ====================
 * 
 * Provides mock data for export jobs with stable IDs and realistic timestamps.
 */

const now = new Date();
const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000);
const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

// Mock export jobs storage (simulating backend state)
let mockJobs: ExportJob[] = [
  // Completed RLMF export
  {
    id: 'export_rlmf_001',
    kind: 'rlmf',
    status: 'completed',
    createdAt: twoDaysAgo.toISOString(),
    completedAt: new Date(twoDaysAgo.getTime() + 45 * 60 * 1000).toISOString(),
    scope: {
      scope: 'my',
      timelineIds: ['tl_oil_hormuz_001', 'tl_fed_rate_jan26'],
      dateFrom: new Date(twoDaysAgo.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      dateTo: twoDaysAgo.toISOString(),
    },
    filter: {
      kind: 'rlmf',
      seedTier: 'tier1',
      minForkCount: 5,
      maxEpisodeDurationSec: 3600,
    },
    rowCount: 12450,
    byteSize: 2456789,
    downloadUrl: 'https://exports.echelon.io/rlmf/export_rlmf_001.jsonl',
  },
  // Completed Human Judgement export
  {
    id: 'export_hj_001',
    kind: 'human_judgement',
    status: 'completed',
    createdAt: oneDayAgo.toISOString(),
    completedAt: new Date(oneDayAgo.getTime() + 30 * 60 * 1000).toISOString(),
    scope: {
      scope: 'workspace',
      theatreIds: ['theatre_001'],
      dateFrom: new Date(oneDayAgo.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      dateTo: oneDayAgo.toISOString(),
    },
    filter: {
      kind: 'human_judgement',
      paradoxOnly: true,
      seedTier: 'tier2',
    },
    rowCount: 3420,
    byteSize: 892345,
    downloadUrl: 'https://exports.echelon.io/human_judgement/export_hj_001.jsonl',
  },
  // Running export
  {
    id: 'export_audit_001',
    kind: 'audit_trace',
    status: 'running',
    createdAt: threeHoursAgo.toISOString(),
    scope: {
      scope: 'global',
      dateFrom: new Date(threeHoursAgo.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      dateTo: threeHoursAgo.toISOString(),
    },
    filter: {
      kind: 'audit_trace',
      oodOnly: true,
    },
    rowCount: undefined,
    byteSize: undefined,
  },
];

/**
 * List Export Jobs
 * 
 * Returns all export jobs for the current user.
 * 
 * @returns Promise resolving to array of ExportJob
 */
export async function listExportJobs(): Promise<ExportJob[]> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 150));
  
  // Return jobs sorted by creation date (newest first)
  return [...mockJobs].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
}

/**
 * Create Export Job
 * 
 * Creates a new export job with the specified scope and filter.
 * 
 * @param input - Export job configuration
 * @param input.scope - Scope of data to export
 * @param input.filter - Filters to apply to the export
 * @returns Promise resolving to the created ExportJob
 */
export async function createExportJob(input: {
  scope: ExportScope;
  filter: ExportFilter;
}): Promise<ExportJob> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  // Generate stable ID based on kind and timestamp
  const timestamp = Date.now();
  const kindPrefix = input.filter.kind === 'rlmf' ? 'rlmf' : 
                     input.filter.kind === 'human_judgement' ? 'hj' : 'audit';
  const newJob: ExportJob = {
    id: `export_${kindPrefix}_${timestamp}`,
    kind: input.filter.kind,
    status: 'queued',
    createdAt: new Date().toISOString(),
    scope: input.scope,
    filter: input.filter,
  };
  
  // Add to mock storage
  mockJobs.push(newJob);
  
  return newJob;
}

/**
 * Get Dataset Preview
 * 
 * Returns a preview of a dataset including schema and sample rows.
 * 
 * @param kind - Type of dataset to preview
 * @returns Promise resolving to DatasetPreview
 */
export async function getDatasetPreview(
  kind: ExportDatasetKind
): Promise<DatasetPreview> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 100));
  
  if (kind === 'rlmf') {
    const fields: DatasetSchemaField[] = [
      {
        name: 'episode_id',
        type: 'string',
        description: 'Unique identifier for the episode',
      },
      {
        name: 'timeline_id',
        type: 'string',
        description: 'ID of the timeline this episode belongs to',
      },
      {
        name: 'agent_id',
        type: 'string',
        description: 'ID of the agent that generated this episode',
      },
      {
        name: 'timestamp',
        type: 'string',
        description: 'ISO 8601 timestamp when the episode occurred',
      },
      {
        name: 'actions',
        type: 'array',
        description: 'Array of actions taken by the agent during the episode',
      },
      {
        name: 'rewards',
        type: 'array',
        description: 'Reward signals received for each action',
      },
      {
        name: 'state_features',
        type: 'object',
        description: 'State features including stability, logic_gap, entropy_rate',
      },
      {
        name: 'fork_count',
        type: 'number',
        description: 'Number of forks that occurred during the episode',
      },
      {
        name: 'episode_duration_sec',
        type: 'number',
        description: 'Duration of the episode in seconds',
      },
      {
        name: 'seed_tier',
        type: 'string',
        description: 'Seed tier classification (tier1, tier2, tier3)',
      },
    ];
    
    const sampleRows: Record<string, any>[] = [
      {
        episode_id: 'ep_001',
        timeline_id: 'tl_oil_hormuz_001',
        agent_id: 'agent_alpha',
        timestamp: twoDaysAgo.toISOString(),
        actions: ['BUY_YES', 'DEPLOY_SHIELD', 'EXTRACT_PARADOX'],
        rewards: [0.5, -0.2, 1.0],
        state_features: {
          stability: 54.7,
          logic_gap: 42,
          entropy_rate: -2.1,
        },
        fork_count: 8,
        episode_duration_sec: 2847,
        seed_tier: 'tier1',
      },
      {
        episode_id: 'ep_002',
        timeline_id: 'tl_fed_rate_jan26',
        agent_id: 'agent_beta',
        timestamp: new Date(twoDaysAgo.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        actions: ['BUY_NO', 'SABOTAGE'],
        rewards: [0.3, -0.5],
        state_features: {
          stability: 89.2,
          logic_gap: 8,
          entropy_rate: -0.5,
        },
        fork_count: 3,
        episode_duration_sec: 1200,
        seed_tier: 'tier1',
      },
      {
        episode_id: 'ep_003',
        timeline_id: 'tl_oil_hormuz_001',
        agent_id: 'agent_gamma',
        timestamp: new Date(twoDaysAgo.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        actions: ['BUY_YES', 'MONITOR'],
        rewards: [0.1, 0.0],
        state_features: {
          stability: 58.3,
          logic_gap: 35,
          entropy_rate: -1.8,
        },
        fork_count: 5,
        episode_duration_sec: 2100,
        seed_tier: 'tier2',
      },
    ];
    
    return {
      kind: 'rlmf',
      schemaVersion: 'rlmf_v0.2',
      fields,
      sampleRows,
    };
  }
  
  if (kind === 'human_judgement') {
    const fields: DatasetSchemaField[] = [
      {
        name: 'judgement_id',
        type: 'string',
        description: 'Unique identifier for the human judgement',
      },
      {
        name: 'timeline_id',
        type: 'string',
        description: 'ID of the timeline being judged',
      },
      {
        name: 'judge_id',
        type: 'string',
        description: 'ID of the human judge',
      },
      {
        name: 'timestamp',
        type: 'string',
        description: 'ISO 8601 timestamp when the judgement was made',
      },
      {
        name: 'paradox_active',
        type: 'boolean',
        description: 'Whether a paradox was active at the time of judgement',
      },
      {
        name: 'stability_rating',
        type: 'number',
        description: 'Human-rated stability score (0-100)',
      },
      {
        name: 'logic_gap_rating',
        type: 'number',
        description: 'Human-rated logic gap score (0-100)',
      },
      {
        name: 'confidence',
        type: 'number',
        description: 'Judge confidence level (0-1)',
      },
      {
        name: 'reasoning',
        type: 'string',
        description: 'Free-text reasoning provided by the judge',
      },
      {
        name: 'seed_tier',
        type: 'string',
        description: 'Seed tier classification',
      },
    ];
    
    const sampleRows: Record<string, any>[] = [
      {
        judgement_id: 'judge_001',
        timeline_id: 'tl_oil_hormuz_001',
        judge_id: 'judge_alpha',
        timestamp: oneDayAgo.toISOString(),
        paradox_active: true,
        stability_rating: 45,
        logic_gap_rating: 65,
        confidence: 0.85,
        reasoning: 'Timeline shows clear signs of instability. Multiple contradictory signals from OSINT sources. Paradox risk is high.',
        seed_tier: 'tier2',
      },
      {
        judgement_id: 'judge_002',
        timeline_id: 'tl_fed_rate_jan26',
        judge_id: 'judge_beta',
        timestamp: new Date(oneDayAgo.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        paradox_active: false,
        stability_rating: 88,
        logic_gap_rating: 12,
        confidence: 0.92,
        reasoning: 'Stable timeline with strong consensus. Low logic gap indicates good signal alignment.',
        seed_tier: 'tier1',
      },
      {
        judgement_id: 'judge_003',
        timeline_id: 'tl_oil_hormuz_001',
        judge_id: 'judge_gamma',
        timestamp: new Date(oneDayAgo.getTime() - 4 * 60 * 60 * 1000).toISOString(),
        paradox_active: true,
        stability_rating: 52,
        logic_gap_rating: 48,
        confidence: 0.78,
        reasoning: 'Moderate stability but logic gap is concerning. Paradox extraction may be necessary.',
        seed_tier: 'tier2',
      },
    ];
    
    return {
      kind: 'human_judgement',
      schemaVersion: 'human_judgement_v0.1',
      fields,
      sampleRows,
    };
  }
  
  // Default: audit_trace
  const fields: DatasetSchemaField[] = [
    {
      name: 'audit_id',
      type: 'string',
      description: 'Unique identifier for the audit event',
    },
    {
      name: 'event_type',
      type: 'string',
      description: 'Type of audit event (trade, sabotage, paradox, etc.)',
    },
    {
      name: 'timeline_id',
      type: 'string',
      description: 'ID of the timeline where the event occurred',
    },
    {
      name: 'agent_id',
      type: 'string',
      description: 'ID of the agent that triggered the event',
    },
    {
      name: 'timestamp',
      type: 'string',
      description: 'ISO 8601 timestamp when the event occurred',
    },
    {
      name: 'details',
      type: 'object',
      description: 'Event-specific details and metadata',
    },
    {
      name: 'is_ood',
      type: 'boolean',
      description: 'Whether this event is out-of-distribution',
    },
  ];
  
  const sampleRows: Record<string, any>[] = [
    {
      audit_id: 'audit_001',
      event_type: 'trade',
      timeline_id: 'tl_oil_hormuz_001',
      agent_id: 'agent_alpha',
      timestamp: threeHoursAgo.toISOString(),
      details: {
        action: 'BUY_YES',
        amount: 1000,
        price: 0.45,
      },
      is_ood: false,
    },
    {
      audit_id: 'audit_002',
      event_type: 'sabotage',
      timeline_id: 'tl_fed_rate_jan26',
      agent_id: 'agent_shadow',
      timestamp: new Date(threeHoursAgo.getTime() - 30 * 60 * 1000).toISOString(),
      details: {
        sabotage_type: 'Evidence Injection',
        stake_amount: 2000,
      },
      is_ood: true,
    },
  ];
  
  return {
    kind: 'audit_trace',
    schemaVersion: 'audit_trace_v0.1',
    fields,
    sampleRows,
  };
}
