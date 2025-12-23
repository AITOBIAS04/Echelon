import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, Shield, AlertTriangle } from 'lucide-react';

export function TimelineDetail() {
  const { timelineId } = useParams();

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <Link 
          to="/sigint" 
          className="flex items-center gap-2 text-terminal-muted hover:text-echelon-cyan mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to SIGINT
        </Link>

        <div className="terminal-panel p-6">
          <h1 className="text-2xl font-bold text-echelon-cyan mb-2">
            Timeline: {timelineId}
          </h1>
          <p className="text-terminal-muted">
            Detailed timeline trading view coming soon. This will include:
          </p>
          <ul className="mt-4 space-y-2 text-sm text-terminal-muted">
            <li className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-echelon-green" />
              Buy YES button
            </li>
            <li className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-echelon-red" />
              Buy NO button
            </li>
            <li className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-echelon-cyan" />
              Deploy Shield action
            </li>
            <li className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-echelon-amber" />
              Paradox status & extraction
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default TimelineDetail;
