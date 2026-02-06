import { useState, useEffect } from 'react';
import { X, Search, AlertTriangle, Crosshair, Globe, MessageSquare, FileText, Zap, Activity, ShieldAlert } from 'lucide-react';
import { getArchetypeTheme } from '../../theme/agentsTheme';

interface Agent {
  id: string;
  name: string;
  archetype: string;
  sanity?: number;
}

interface TaskAgentModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
}

const MISSION_TEMPLATES = [
  {
    id: 'dark-fleet',
    name: 'Track Dark Fleet Vessel',
    description: 'Monitor AIS signals for vessels going dark near specified region',
    icon: Globe,
    cost: 150,
    sanityCost: 8,
    duration: '2-4 hours',
  },
  {
    id: 'social-sentiment',
    name: 'Social Sentiment Scan',
    description: 'Analyze Twitter/X, Reddit, Telegram for keyword sentiment spikes',
    icon: MessageSquare,
    cost: 100,
    sanityCost: 5,
    duration: '1-2 hours',
  },
  {
    id: 'executive-movement',
    name: 'Executive Movement Intel',
    description: 'Track private jet movements and correlate with corporate events',
    icon: Crosshair,
    cost: 250,
    sanityCost: 12,
    duration: '4-8 hours',
  },
  {
    id: 'patent-watch',
    name: 'Patent/Filing Watch',
    description: 'Monitor USPTO, SEC filings for specified company or technology',
    icon: FileText,
    cost: 120,
    sanityCost: 6,
    duration: '6-12 hours',
  },
  {
    id: 'custom',
    name: 'Custom OSINT Query',
    description: 'Define your own intelligence gathering mission',
    icon: Search,
    cost: 200,
    sanityCost: 10,
    duration: 'Variable',
  },
];

export function TaskAgentModal({ agent, isOpen, onClose }: TaskAgentModalProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [customQuery, setCustomQuery] = useState('');
  const [targetUrl, setTargetUrl] = useState('');

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const selectedMission = MISSION_TEMPLATES.find(t => t.id === selectedTemplate);
  const agentSanity = agent.sanity ?? 75;
  const canAffordSanity = selectedMission ? agentSanity >= selectedMission.sanityCost : true;

  return (
    <>
      {/* Glassmorphism Overlay */}
      <div 
        className="fixed inset-0 bg-terminal-bg/80 backdrop-blur-sm z-[300]"
        style={{ pointerEvents: 'auto' }}
        onClick={onClose}
      />
      
      {/* Modal content */}
      <div 
        className="fixed inset-0 z-[310] flex items-center justify-center p-4 pointer-events-none"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div 
          className="bg-terminal-bg border border-glass-border rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
        {/* Header */}
        <div className="p-5 border-b border-glass-border flex items-center justify-between bg-glass-card backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-signal-action/10 rounded-full flex items-center justify-center border border-signal-action/20">
              <Search className="w-5 h-5 text-signal-action" />
            </div>
            <div>
              <h3 className="text-white font-sans font-bold tracking-tight text-lg">TASK AGENT</h3>
              <p className="text-signal-muted text-xs font-sans">Deploy {agent.name} on intelligence mission</p>
            </div>
          </div>
          <button onClick={onClose} className="text-signal-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content - Bento Grid Layout */}
        <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
            
            {/* Bento Grid Top Section: Mission Map & Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                {/* Large Card: Active Mission Map */}
                <div className="md:col-span-2 bg-glass-card border border-glass-border rounded-xl p-5 relative overflow-hidden backdrop-blur-md group hover:border-glass-border-light transition-all duration-300">
                    <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                        <Globe className="w-32 h-32" />
                    </div>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-sans font-medium text-terminal-text-secondary flex items-center gap-2">
                            <Globe className="w-4 h-4 text-signal-action" />
                            ACTIVE MISSION MAP
                        </h3>
                        <span className="text-[10px] font-mono text-signal-success border border-signal-success/30 px-2 py-0.5 rounded-full bg-signal-success/10">
                            ONLINE
                        </span>
                    </div>
                    
                    {/* Visual Placeholder for Map */}
                    <div className="h-32 w-full rounded-lg border border-glass-border bg-black/40 relative overflow-hidden flex items-center justify-center">
                        <div className="absolute inset-0 grid grid-cols-12 grid-rows-6 opacity-20 pointer-events-none">
                            {Array.from({length: 72}).map((_, i) => (
                                <div key={i} className="border-[0.5px] border-signal-action/10" />
                            ))}
                        </div>
                        {/* Radar Scan Effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-signal-action/5 to-transparent w-full h-full animate-[shimmer_3s_infinite] -skew-x-12 translate-x-[-100%]" />
                        
                        <div className="flex items-center gap-3 z-10">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-signal-action opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-signal-action"></span>
                            </span>
                            <span className="font-mono text-xs text-signal-action tracking-widest">GLOBAL_INTEL_LAYER_V4</span>
                        </div>
                    </div>
                </div>

                {/* Right Column: Stats Cards */}
                <div className="space-y-4">
                    {/* Net APY Card */}
                    <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md flex flex-col justify-center h-[calc(50%-0.5rem)] hover:border-glass-border-light transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-sans text-terminal-text-secondary">NET APY</span>
                            <Activity className="w-4 h-4 text-signal-success opacity-80" />
                        </div>
                        <div className="text-2xl font-mono font-bold text-signal-success tracking-tight">
                            +24.5%
                        </div>
                    </div>

                    {/* Paradox Level Card */}
                    <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md flex flex-col justify-center h-[calc(50%-0.5rem)] hover:border-glass-border-light transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-sans text-terminal-text-secondary">PARADOX LEVEL</span>
                            <ShieldAlert className="w-4 h-4 text-signal-risk opacity-80" />
                        </div>
                        <div className="text-2xl font-mono font-bold text-signal-risk tracking-tight">
                            12.4%
                        </div>
                    </div>
                </div>
            </div>

          {/* Agent Identity & Status */}
          <div className="bg-glass-card border border-glass-border rounded-xl p-4 mb-8 backdrop-blur-md">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${getArchetypeTheme(agent.archetype).bgClass} ${getArchetypeTheme(agent.archetype).borderClass}`}>
                  {(() => { const theme = getArchetypeTheme(agent.archetype); const Icon = theme.icon; return <Icon className={`w-4 h-4 ${theme.textClass}`} />; })()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                      <span className="text-sm font-sans font-bold text-white">{agent.name}</span>
                      <span className="text-[10px] font-mono text-signal-muted uppercase tracking-wider border border-glass-border px-1.5 rounded">{agent.archetype}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-sans text-terminal-text-secondary mr-2">SANITY INTEGRITY</span>
                <span className={`font-mono font-bold ${agentSanity > 50 ? 'text-signal-success' : 'text-signal-risk'}`}>
                    {agentSanity}%
                </span>
              </div>
            </div>
            {/* Progress Bar */}
            <div className="w-full bg-terminal-border/50 rounded-full h-1.5 overflow-hidden">
               <div 
                  className={`h-full rounded-full transition-all duration-500 ${agentSanity > 50 ? 'bg-signal-success' : agentSanity > 25 ? 'bg-signal-risk' : 'bg-signal-sabotage'}`}
                  style={{ width: `${agentSanity}%` }}
               />
            </div>
          </div>

          {/* Mission Selection Grid */}
          <div className="mb-4">
            <h4 className="text-xs font-sans font-semibold text-terminal-text-muted uppercase tracking-widest mb-4 ml-1">Select Operation</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {MISSION_TEMPLATES.map((template) => {
                const Icon = template.icon;
                const isSelected = selectedTemplate === template.id;
                return (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`p-4 rounded-xl border text-left transition-all duration-200 group relative overflow-hidden ${
                      isSelected 
                        ? 'bg-signal-action/10 border-signal-action/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
                        : 'bg-glass-card border-glass-border hover:border-signal-action/30 hover:bg-glass-card/80'
                    }`}
                  >
                    <div className="flex items-start gap-4 relative z-10">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${isSelected ? 'bg-signal-action/20' : 'bg-white/5 group-hover:bg-white/10'}`}>
                        <Icon className={`w-5 h-5 ${isSelected ? 'text-signal-action' : 'text-terminal-text-secondary group-hover:text-gray-200'}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className={`font-sans font-semibold text-sm truncate pr-2 ${isSelected ? 'text-white' : 'text-gray-300 group-hover:text-white'}`}>
                            {template.name}
                          </span>
                        </div>
                        <p className="text-signal-muted text-xs line-clamp-2 mb-3 font-sans h-8">{template.description}</p>
                        
                        <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                            <span className="text-signal-risk text-xs font-mono flex items-center gap-1">
                                <Zap className="w-3 h-3" />
                                {template.cost}
                            </span>
                            <span className={`text-xs font-mono flex items-center gap-1 ${isSelected ? 'text-signal-action' : 'text-terminal-text-muted'}`}>
                                <Activity className="w-3 h-3" />
                                -{template.sanityCost} SAN
                            </span>
                            <span className="text-terminal-text-muted text-[10px] font-sans ml-auto">
                                {template.duration}
                            </span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Query Input */}
          {selectedTemplate === 'custom' && (
            <div className="mb-6 p-4 bg-glass-card border border-glass-border rounded-xl backdrop-blur-md animate-fade-in">
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">Target URL (Optional)</label>
                  <input
                    type="text"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    placeholder="https://twitter.com/... or https://discord.gg/..."
                    className="w-full bg-terminal-bg border border-glass-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-signal-action focus:outline-none focus:ring-1 focus:ring-signal-action/50 transition-all font-sans"
                  />
                </div>
                <div>
                  <label className="text-xs font-sans text-terminal-text-muted uppercase tracking-wide block mb-2">Intelligence Query</label>
                  <textarea
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    placeholder="e.g., Monitor all mentions of 'Project Titan' in Apple-related Discord servers..."
                    rows={3}
                    className="w-full bg-terminal-bg border border-glass-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-signal-action focus:outline-none focus:ring-1 focus:ring-signal-action/50 transition-all resize-none font-sans"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Cost Summary & Warning */}
          {selectedMission && (
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-glass-card border border-glass-border rounded-xl p-4 backdrop-blur-md">
                    <h4 className="text-xs text-terminal-text-muted font-sans uppercase tracking-wide mb-3">Mission Analysis</h4>
                     <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                        <span className="text-terminal-text-secondary font-sans">Token Cost</span>
                        <span className="text-signal-risk font-mono font-bold flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            {selectedMission.cost} $ECH
                        </span>
                        </div>
                        <div className="flex justify-between text-sm">
                        <span className="text-terminal-text-secondary font-sans">Sanity Impact</span>
                        <span className={`font-mono font-bold ${canAffordSanity ? 'text-signal-action' : 'text-signal-sabotage'}`}>
                            -{selectedMission.sanityCost} SAN
                        </span>
                        </div>
                    </div>
                </div>

                {!canAffordSanity && (
                    <div className="bg-signal-sabotage/10 border border-signal-sabotage/20 rounded-xl p-4 flex items-center justify-center text-center">
                        <div className="flex flex-col items-center gap-1">
                            <AlertTriangle className="w-5 h-5 text-signal-sabotage mb-1" />
                            <span className="text-sm font-bold text-signal-sabotage font-sans">Insufficient Sanity</span>
                            <span className="text-xs text-signal-sabotage/80">Recover agent before deploying</span>
                        </div>
                    </div>
                )}
             </div>
          )}

          {/* Warning Banner */}
          <div className="bg-signal-risk/5 border border-signal-risk/20 rounded-lg p-3 flex items-start gap-3">
             <AlertTriangle className="w-4 h-4 text-signal-risk mt-0.5 flex-shrink-0" />
             <div>
               <p className="text-signal-risk text-sm font-bold font-sans">Wallet Connection Required</p>
               <p className="text-terminal-text-secondary text-xs mt-0.5 font-sans">
                 Connect wallet and hold $ECHELON to deploy intelligence missions.
               </p>
             </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-5 border-t border-glass-border bg-glass-card backdrop-blur-md flex gap-3 rounded-b-xl">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-white/5 text-gray-300 rounded-lg font-bold hover:bg-white/10 transition-colors font-sans text-sm"
          >
            CANCEL
          </button>
          <button
            disabled
            className="flex-1 px-4 py-3 bg-signal-action/10 border border-signal-action/20 text-signal-action/50 rounded-lg font-bold cursor-not-allowed flex items-center justify-center gap-2 font-sans text-sm"
          >
            <Search className="w-4 h-4" />
            CONNECT WALLET TO DEPLOY
          </button>
        </div>
      </div>
      </div>
    </>
  );
}

export default TaskAgentModal;