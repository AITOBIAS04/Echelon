import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { AgentPerformanceDashboard } from './AgentPerformanceDashboard';
import { ArchetypeComparison } from './ArchetypeComparison';

export function AgentDetail() {
  const { agentId } = useParams();

  if (!agentId) {
    return (
      <div className="h-full p-6 text-terminal-text-muted text-xs">
        No agent ID provided.
      </div>
    );
  }

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <Link
          to="/agents"
          className="flex items-center gap-2 text-terminal-text-muted hover:text-echelon-cyan mb-6 transition text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Roster
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main — Agent detail + trade history + genome */}
          <div className="lg:col-span-2">
            <AgentPerformanceDashboard agentId={agentId} />
          </div>

          {/* Sidebar — Archetype comparison */}
          <div>
            <ArchetypeComparison />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentDetail;
