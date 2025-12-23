import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Activity, TrendingUp, Brain, Zap } from 'lucide-react';

export function AgentDetail() {
  const { agentId } = useParams();

  // In production, fetch agent data based on agentId
  // For now, show placeholder

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <Link 
          to="/agents" 
          className="flex items-center gap-2 text-terminal-muted hover:text-echelon-cyan mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Roster
        </Link>

        <div className="terminal-panel p-6">
          <h1 className="text-2xl font-bold text-echelon-cyan mb-2">
            Agent: {agentId}
          </h1>
          <p className="text-terminal-muted">
            Detailed agent view coming soon. This will show:
          </p>
          <ul className="mt-4 space-y-2 text-sm text-terminal-muted">
            <li className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-echelon-cyan" />
              Complete trading history
            </li>
            <li className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-echelon-green" />
              Performance charts
            </li>
            <li className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-echelon-purple" />
              Genome traits
            </li>
            <li className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-echelon-amber" />
              Hire this agent button
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default AgentDetail;
