import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export function AgentDetail() {
  const { agentId } = useParams();

  // In real app, fetch agent data by ID

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      <Link
        to="/agents"
        className="flex items-center gap-2 text-terminal-muted hover:text-echelon-cyan transition w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back to Roster</span>
      </Link>

      <div className="terminal-panel p-6">
        <h1 className="text-2xl font-display text-terminal-text mb-2">
          Agent Detail: {agentId}
        </h1>
        <p className="text-terminal-muted">
          Full agent profile, performance history, and hiring interface coming in Phase 2.
        </p>
      </div>
    </div>
  );
}

