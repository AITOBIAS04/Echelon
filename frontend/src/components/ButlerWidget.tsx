import { useState } from 'react';
import { MessageSquare, X, ExternalLink, Terminal } from 'lucide-react';

export function ButlerWidget() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="fixed bottom-24 md:bottom-6 right-4 md:right-6 z-[100]">
      {/* Expanded Panel */}
      {isExpanded && (
        <div className="mb-4 w-80 bg-terminal-panel border border-purple-500/50 rounded-lg shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
          {/* Header */}
          <div className="p-4 bg-purple-900/30 border-b border-status-paradox/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-status-paradox" />
              <span className="text-status-paradox font-bold">VIRTUALS BUTLER</span>
            </div>
            <button 
              onClick={() => setIsExpanded(false)}
              className="text-terminal-text-muted hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-terminal-text-secondary text-sm mb-4">
              Chat with Echelon agents directly on X. Query timelines, hire spies, and execute trades.
            </p>

            {/* Example Commands */}
            <div className="space-y-2 mb-4">
              <p className="text-xs text-terminal-text-muted uppercase tracking-wide">Example Commands</p>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-echelon-cyan">
                @VirtualsButler show trending timelines
              </div>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-echelon-cyan">
                @VirtualsButler hire CARDINAL for intel
              </div>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-echelon-cyan">
                @VirtualsButler paradox status
              </div>
            </div>

            {/* CTA Button */}
            <a
              href="https://x.com/VirtualsButler"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-900/50 border border-purple-500/50 text-status-paradox rounded-lg font-bold hover:bg-purple-900/70 transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              OPEN BUTLER ON X
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Footer */}
          <div className="px-4 py-2 bg-gray-900/50 border-t border-terminal-border text-center">
            <p className="text-terminal-text-muted text-xs">
              Powered by <span className="text-status-paradox">Virtuals Protocol</span>
            </p>
          </div>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center shadow-lg transition-all relative ${
          isExpanded 
            ? 'bg-purple-600 text-white' 
            : 'bg-purple-900/80 border border-purple-500/50 text-status-paradox hover:bg-purple-900 hover:scale-110'
        }`}
      >
        {isExpanded ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageSquare className="w-6 h-6" />
        )}
        
        {/* Pulse indicator when collapsed */}
        {!isExpanded && (
          <span className="absolute top-0 right-0 w-3 h-3 bg-green-500 rounded-full animate-pulse border-2 border-terminal-bg" />
        )}
      </button>
    </div>
  );
}

export default ButlerWidget;

