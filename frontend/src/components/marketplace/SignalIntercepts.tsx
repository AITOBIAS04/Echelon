import { useState } from 'react';
import { Activity, Eye, Zap, Target, Globe, Ghost, Radio } from 'lucide-react';
import { clsx } from 'clsx';
import type { Intercept } from '../../types/marketplace';

interface SignalInterceptsProps {
  intercepts: Intercept[];
  onViewAll?: () => void;
  onInterceptClick?: (intercept: Intercept) => void;
}

// Map agent names to lucide icons
const AGENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  CARDINAL: Eye,
  MEGALODON: Target,
  CHAMELEON: Zap,
  VULTURE: Radio,
  MEDUSA: Globe,
  ATLAS: Globe,
  PHANTOM: Ghost,
  NEXUS: Radio,
};

/**
 * Get agent icon component
 */
function getAgentIcon(agent: string): React.ComponentType<{ className?: string }> {
  return AGENT_ICONS[agent] || Radio;
}

/**
 * Get action button style
 */
function getActionStyle(action: string): string {
  const styles: Record<string, string> = {
    Theatre: 'text-[#3B82F6] hover:bg-[rgba(59,130,246,0.1)] border-[rgba(59,130,246,0.3)]',
    Trade: 'text-[#4ADE80] hover:bg-[rgba(74,222,128,0.1)] border-[rgba(74,222,128,0.3)]',
    Shield: 'text-[#FACC15] hover:bg-[rgba(250,204,21,0.1)] border-[rgba(250,204,21,0.3)]',
    Adjust: 'text-[#8B5CF6] hover:bg-[rgba(139,92,246,0.1)] border-[rgba(139,92,246,0.3)]',
    Verify: 'text-[#22D3EE] hover:bg-[rgba(34,211,238,0.1)] border-[rgba(34,211,238,0.3)]',
    Monitor: 'text-[#64748B] hover:bg-[#151719] border-[#26292E]',
  };

  return styles[action] || styles.Monitor;
}

/**
 * SignalIntercepts Component
 * 
 * Sidebar panel showing real-time signal intercepts from AI agents:
 * - Agent name and icon
 * - Timestamp
 * - Theatre and content
 * - Action buttons
 */
export function SignalIntercepts({ intercepts, onViewAll, onInterceptClick }: SignalInterceptsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (intercepts.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col border-b border-[#26292E]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#151719]/95 backdrop-blur-sm px-4 py-3 border-b border-[#26292E]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#4ADE80] animate-pulse" />
            <span className="text-xs font-bold text-[#F1F5F9] uppercase tracking-wider">
              Signal Intercepts
            </span>
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-[rgba(251,113,133,0.2)] border border-[rgba(251,113,133,0.3)] rounded text-[9px] font-bold text-[#FB7185] uppercase">
              <span className="w-1 h-1 bg-[#FB7185] rounded-full animate-pulse" />
              LIVE
            </span>
          </div>
          {onViewAll && (
            <button
              onClick={onViewAll}
              className="text-[10px] text-[#3B82F6] hover:underline"
            >
              Full Feed →
            </button>
          )}
        </div>
      </div>

      {/* Intercepts List */}
      <div className="flex-1 overflow-y-auto">
        {intercepts.map((intercept, index) => {
          const isExpanded = expandedId === intercept.id;
          const AgentIcon = getAgentIcon(intercept.agent);

          return (
            <div
              key={intercept.id || index}
              className={clsx(
                'border-b border-[#26292E] last:border-b-0',
                'transition-colors hover:bg-[#1A1D21]/50 cursor-pointer',
                isExpanded && 'bg-[#1A1D21]/50'
              )}
              onClick={() => {
                setExpandedId(isExpanded ? null : (intercept.id || String(index)));
                onInterceptClick?.(intercept);
              }}
            >
              <div className="p-3">
                {/* Header: Agent + Time */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AgentIcon className="w-4 h-4 text-[#64748B]" />
                    <span className="text-xs font-bold font-mono text-[#F1F5F9]">
                      {intercept.agent}
                    </span>
                    <span className="text-[10px] text-[#64748B] px-1.5 py-0.5 bg-[#121417] rounded border border-[#26292E]">
                      {intercept.theatre}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#64748B]">
                    {intercept.time}
                  </span>
                </div>

                {/* Content */}
                <p className="text-xs text-[#94A3B8] leading-relaxed mb-3">
                  {intercept.content}
                </p>

                {/* Actions */}
                <div className="flex items-center gap-1.5">
                  {intercept.actions.map((action, actionIndex) => (
                    <button
                      key={actionIndex}
                      onClick={(e) => {
                        e.stopPropagation();
                        // Handle action click
                      }}
                      className={clsx(
                        'px-2 py-1 text-[10px] font-medium uppercase tracking-wider rounded border transition-all',
                        getActionStyle(action)
                      )}
                    >
                      {action}
                    </button>
))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Source Footer */}
      <div className="px-4 py-2 bg-[#121417] border-t border-[#26292E]">
        <p className="text-[10px] text-center font-mono text-[#64748B]">
          SRC: OSINT / SENSORS / ON-CHAIN
        </p>
      </div>
    </div>
  );
}
