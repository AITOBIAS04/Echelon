import { useState } from 'react';
import { MessageSquare, X, ExternalLink, Terminal } from 'lucide-react';

export function ButlerWidget() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="fixed bottom-24 md:bottom-6 right-4 md:right-6 z-[100]">
      {/* Expanded Panel */}
      {isExpanded && (
        <div className="mb-4 w-80 bg-[#0D0D0D] border border-purple-500/50 rounded-lg shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
          {/* Header */}
          <div className="p-4 bg-purple-900/30 border-b border-purple-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-purple-400" />
              <span className="text-purple-400 font-bold">VIRTUALS BUTLER</span>
            </div>
            <button 
              onClick={() => setIsExpanded(false)}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-gray-400 text-sm mb-4">
              Chat with Echelon agents directly on X. Query timelines, hire spies, and execute trades.
            </p>

            {/* Example Commands */}
            <div className="space-y-2 mb-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Example Commands</p>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-cyan-400">
                @VirtualsButler show trending timelines
              </div>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-cyan-400">
                @VirtualsButler hire CARDINAL for intel
              </div>
              <div className="bg-gray-900 rounded p-2 font-mono text-xs text-cyan-400">
                @VirtualsButler paradox status
              </div>
            </div>

            {/* CTA Button */}
            <a
              href="https://x.com/VirtualsButler"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-900/50 border border-purple-500/50 text-purple-400 rounded-lg font-bold hover:bg-purple-900/70 transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              OPEN BUTLER ON X
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Footer */}
          <div className="px-4 py-2 bg-gray-900/50 border-t border-gray-800 text-center">
            <p className="text-gray-600 text-xs">
              Powered by <span className="text-purple-400">Virtuals Protocol</span>
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
            : 'bg-purple-900/80 border border-purple-500/50 text-purple-400 hover:bg-purple-900 hover:scale-110'
        }`}
      >
        {isExpanded ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageSquare className="w-6 h-6" />
        )}
        
        {/* Pulse indicator when collapsed */}
        {!isExpanded && (
          <span className="absolute top-0 right-0 w-3 h-3 bg-green-500 rounded-full animate-pulse border-2 border-[#0D0D0D]" />
        )}
      </button>
    </div>
  );
}

export default ButlerWidget;

