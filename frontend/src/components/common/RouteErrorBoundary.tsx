import { useRouteError, Link } from 'react-router-dom';
import { Home, Users, RefreshCw } from 'lucide-react';

export function RouteErrorBoundary() {
  const error = useRouteError();

  const is404 = error instanceof Error && error.message.includes('404');

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 text-center">
      <div className="max-w-md">
        <h1 className="text-2xl font-bold text-terminal-text mb-2">
          {is404 ? 'Page not found' : 'Unexpected error'}
        </h1>
        <p className="text-terminal-muted mb-6">
          {is404
            ? 'The page you are looking for does not exist or has been moved.'
            : 'An error occurred while loading this page. Please try again.'}
        </p>

        <div className="flex items-center justify-center gap-3">
          <Link
            to="/marketplace"
            className="flex items-center gap-2 px-4 py-2 bg-echelon-cyan/20 border border-echelon-cyan/50 text-echelon-cyan rounded-lg text-sm font-semibold hover:bg-echelon-cyan/30 transition-colors"
          >
            <Home className="w-4 h-4" />
            Marketplace
          </Link>
          <Link
            to="/agents"
            className="flex items-center gap-2 px-4 py-2 bg-terminal-bg border border-terminal-border text-terminal-text rounded-lg text-sm font-semibold hover:border-terminal-muted transition-colors"
          >
            <Users className="w-4 h-4" />
            Agents
          </Link>
        </div>

        {import.meta.env.DEV && error instanceof Error && (
          <details className="mt-8 text-left">
            <summary className="text-xs text-terminal-muted cursor-pointer hover:text-terminal-text">
              Developer details
            </summary>
            <pre className="mt-2 p-3 bg-terminal-bg border border-terminal-border rounded text-xs text-terminal-text overflow-auto">
              {error.message}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
