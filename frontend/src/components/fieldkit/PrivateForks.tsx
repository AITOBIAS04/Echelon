import { GitBranch, Plus } from 'lucide-react';

export function PrivateForks() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      <div className="w-16 h-16 rounded-full bg-terminal-panel flex items-center justify-center mb-4">
        <GitBranch className="w-8 h-8 text-echelon-purple" />
      </div>
      <h3 className="text-lg font-medium text-terminal-text mb-2">
        Private Simulation Forks
      </h3>
      <p className="text-sm text-terminal-text-muted mb-6 max-w-md">
        Create "Ghost Forks" of any timeline to test strategies without risking real capital.
        Successful simulations can be published to the global SIGINT feed.
      </p>
      <button className="flex items-center gap-2 px-4 py-2 bg-echelon-purple/20 border border-echelon-purple text-echelon-purple rounded hover:bg-echelon-purple/30 transition">
        <Plus className="w-4 h-4" />
        Create Ghost Fork
      </button>
    </div>
  );
}

