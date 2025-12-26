import { useState } from 'react';
import { X, Search, AlertTriangle, Crosshair, Globe, MessageSquare, FileText, Zap } from 'lucide-react';

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

  if (!isOpen) return null;

  const selectedMission = MISSION_TEMPLATES.find(t => t.id === selectedTemplate);
  const agentSanity = agent.sanity ?? 75;
  const canAffordSanity = selectedMission ? agentSanity >= selectedMission.sanityCost : true;

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />
      
      {/* Modal content - above overlay */}
      <div 
        className="relative z-10 bg-[#0D0D0D] border border-purple-500/50 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-900/50 rounded-full flex items-center justify-center border border-purple-500/30">
              <Search className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-purple-400 font-bold">TASK AGENT</h3>
              <p className="text-gray-500 text-xs">Deploy {agent.name} on intelligence mission</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {/* Agent Status */}
          <div className="bg-gray-900/50 rounded-lg p-3 mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-cyan-400 font-bold">{agent.name}</span>
              <span className="text-gray-500 text-xs uppercase">{agent.archetype}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Sanity:</span>
              <div className="w-20 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${agentSanity > 50 ? 'bg-green-500' : agentSanity > 25 ? 'bg-amber-500' : 'bg-red-500'}`}
                  style={{ width: `${agentSanity}%` }}
                />
              </div>
              <span className="text-xs font-mono text-gray-400">{agentSanity}%</span>
            </div>
          </div>

          {/* Mission Templates */}
          <div className="mb-4">
            <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-3">Select Mission Type</h4>
            <div className="grid grid-cols-1 gap-2">
              {MISSION_TEMPLATES.map((template) => {
                const Icon = template.icon;
                const isSelected = selectedTemplate === template.id;
                return (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      isSelected 
                        ? 'bg-purple-900/30 border-purple-500/50' 
                        : 'bg-gray-900/30 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded flex items-center justify-center ${isSelected ? 'bg-purple-500/20' : 'bg-gray-800'}`}>
                        <Icon className={`w-4 h-4 ${isSelected ? 'text-purple-400' : 'text-gray-500'}`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={`font-bold text-sm ${isSelected ? 'text-purple-400' : 'text-gray-300'}`}>
                            {template.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-amber-400 text-xs font-mono">{template.cost} $ECH</span>
                            <span className="text-purple-400 text-xs font-mono">-{template.sanityCost} SAN</span>
                          </div>
                        </div>
                        <p className="text-gray-500 text-xs mt-1">{template.description}</p>
                        <p className="text-gray-600 text-xs mt-1">Duration: {template.duration}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Query Input (for custom missions) */}
          {selectedTemplate === 'custom' && (
            <div className="mb-4 space-y-3">
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">Target URL (Optional)</label>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="https://twitter.com/... or https://discord.gg/..."
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">Intelligence Query</label>
                <textarea
                  value={customQuery}
                  onChange={(e) => setCustomQuery(e.target.value)}
                  placeholder="e.g., Monitor all mentions of 'Project Titan' in Apple-related Discord servers..."
                  rows={3}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none resize-none"
                />
              </div>
            </div>
          )}

          {/* Cost Summary */}
          {selectedMission && (
            <div className="bg-gray-900 rounded-lg p-4 mb-4">
              <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-3">Mission Cost</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Token Cost</span>
                  <span className="text-amber-400 font-bold flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    {selectedMission.cost} $ECHELON
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Agent Sanity Cost</span>
                  <span className={`font-bold ${canAffordSanity ? 'text-purple-400' : 'text-red-400'}`}>
                    -{selectedMission.sanityCost} Sanity
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Estimated Duration</span>
                  <span className="text-gray-300">{selectedMission.duration}</span>
                </div>
                {!canAffordSanity && (
                  <div className="flex items-center gap-2 text-red-400 text-xs mt-2 pt-2 border-t border-gray-800">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Agent sanity too low for this mission</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Warning */}
          <div className="bg-amber-900/20 border border-amber-500/30 rounded p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-amber-400 text-sm font-bold">Wallet Connection Required</p>
                <p className="text-gray-400 text-xs mt-1">
                  Connect wallet and hold $ECHELON to deploy intelligence missions. Available Q1 2025.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-800 text-gray-300 rounded font-bold hover:bg-gray-700 transition-colors"
          >
            CANCEL
          </button>
          <button
            disabled
            className="flex-1 px-4 py-3 bg-purple-900/30 border border-purple-500/30 text-purple-400/50 rounded font-bold cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            CONNECT WALLET TO DEPLOY
          </button>
        </div>
      </div>
    </div>
  );
}

export default TaskAgentModal;

