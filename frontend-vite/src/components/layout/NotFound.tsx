import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export function NotFound() {
  return (
    <div className="h-full flex flex-col items-center justify-center bg-terminal-bg p-6">
      <div className="terminal-panel p-8 text-center max-w-md">
        <h1 className="text-4xl font-bold text-terminal-text mb-4">
          404
        </h1>
        <h2 className="text-xl font-semibold text-terminal-text mb-2">
          Timeline Not Found
        </h2>
        <p className="text-terminal-muted mb-6">
          The timeline you're looking for doesn't exist or has been terminated.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 rounded hover:bg-echelon-cyan/30 transition text-terminal-text"
        >
          <Home className="w-4 h-4" />
          <span>Return to SIGINT</span>
        </Link>
      </div>
    </div>
  );
}

