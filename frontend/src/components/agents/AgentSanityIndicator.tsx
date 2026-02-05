import { clsx } from 'clsx';

interface AgentSanityProps {
  sanity: number;  // 0-100
  maxSanity?: number;
  name: string;
}

export function AgentSanityIndicator({ sanity, maxSanity = 100, name }: AgentSanityProps) {
  const percentage = (sanity / maxSanity) * 100;
  
  const getSanityStatus = () => {
    if (percentage > 70) return { label: 'STABLE', color: 'green', glow: false };
    if (percentage > 40) return { label: 'STRESSED', color: 'amber', glow: false };
    if (percentage > 20) return { label: 'CRITICAL', color: 'red', glow: true };
    return { label: 'BREAKDOWN', color: 'red', glow: true };
  };
  
  const status = getSanityStatus();
  
  return (
    <div className="mt-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-terminal-text-muted flex items-center gap-1">
          <span>🧠</span> SANITY
        </span>
        <span className={clsx(
          'text-xs font-bold',
          status.color === 'green' && 'text-echelon-green',
          status.color === 'amber' && 'text-echelon-amber',
          status.color === 'red' && 'text-echelon-red',
          status.glow && 'animate-pulse'
        )}>
          {status.label}
        </span>
      </div>
      
      <div className="h-2 bg-terminal-bg rounded-full overflow-hidden">
        <div 
          className={clsx(
            'h-full rounded-full transition-all duration-500',
            status.color === 'green' && 'bg-echelon-green',
            status.color === 'amber' && 'bg-echelon-amber',
            status.color === 'red' && 'bg-echelon-red',
            status.glow && 'animate-pulse'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      <div className="flex justify-between text-xs mt-1">
        <span className={clsx(
          'font-mono',
          status.color === 'green' && 'text-echelon-green',
          status.color === 'amber' && 'text-echelon-amber',
          status.color === 'red' && 'text-echelon-red'
        )}>
          {sanity}/{maxSanity}
        </span>
        
        {percentage <= 20 && (
          <span className="text-echelon-red animate-pulse flex items-center gap-1">
            <span>⚠️</span> BREAKDOWN RISK
          </span>
        )}
      </div>
      
      {/* Critical Warning Banner */}
      {percentage <= 40 && (
        <div className={clsx(
          'mt-2 p-2 rounded text-xs',
          percentage <= 20 
            ? 'bg-echelon-red/20 border border-echelon-red/50 text-echelon-red'
            : 'bg-echelon-amber/20 border border-echelon-amber/50 text-echelon-amber'
        )}>
          {percentage <= 20 
            ? `⚠️ ${name} is near psychological breakdown. High-risk missions may cause permanent damage.`
            : `${name} is under stress. Consider rest or support missions.`
          }
        </div>
      )}
    </div>
  );
}

