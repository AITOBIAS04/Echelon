// Agent Deployment Types — Aligned with backend/schemas/agent_deployment_schemas.py

export type DeploymentStatus =
  | 'ACTIVE'
  | 'PAUSED'
  | 'WITHDRAWN';

export type StrategyProfile =
  | 'AGGRESSIVE'
  | 'BALANCED'
  | 'DEFENSIVE';

export interface AgentDeploymentCreate {
  agent_id: string;
  theatre_id: string;
  strategy_profile?: StrategyProfile;
  config_json?: Record<string, unknown>;
}

export interface StrategyUpdateRequest {
  strategy_profile: StrategyProfile;
}

export interface AgentDeploymentSummary {
  id: string;
  agent_id: string;
  theatre_id: string;
  status: DeploymentStatus;
  strategy_profile: string;
  deployed_at: string;
  created_at: string;
}

export interface AgentDeploymentResponse {
  id: string;
  agent_id: string;
  theatre_id: string;
  status: DeploymentStatus;
  strategy_profile: string;
  deployed_by: string;
  deployed_at: string;
  paused_at: string | null;
  withdrawn_at: string | null;
  routing_hint_snapshot: string | null;
  coherence_gate_status_snapshot: string | null;
  config_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentAuditEvent {
  id: string;
  deployment_id: string;
  event_type: string;
  detail_json: Record<string, unknown> | null;
  created_at: string;
}

export interface DeploymentDetailResponse extends AgentDeploymentResponse {
  audit_events: DeploymentAuditEvent[];
}

export interface DeploymentListResponse {
  deployments: AgentDeploymentSummary[];
  total: number;
  limit: number;
  offset: number;
}
