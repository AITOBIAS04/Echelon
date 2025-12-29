import { useEffect, useState } from 'react';
import { Eye, Send, Lock, X, Target, Clock, Coins } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { clsx } from 'clsx';

interface IntelMission {
  id: string;
  target: string;
  status: 'pending' | 'active' | 'complete' | 'failed';
  agent: string;
  createdAt: Date;
  cost: number;
  results?: string;
}

// Demo missions
const DEMO_MISSIONS: IntelMission[] = [
  {
    id: 'mission_1',
    target: 'Venezuelan Oil Tanker AIS signals',
    status: 'active',
    agent: 'CARDINAL',
    createdAt: new Date(Date.now() - 1800000),
    cost: 150,
  },
  {
    id: 'mission_2', 
    target: 'Fed Governor social media sentiment',
    status: 'complete',
    agent: 'ORACLE',
    createdAt: new Date(Date.now() - 7200000),
    cost: 200,
    results: 'Detected 3 unusual posts suggesting dovish stance. Confidence: 78%'
  }
];

const MISSION_TEMPLATES = [
  { label: 'Track Dark Fleet Vessel', target: 'AIS signals for vessel [NAME]', cost: 150 },
  { label: 'Social Sentiment Scan', target: 'Twitter/X mentions of [TOPIC]', cost: 100 },
  { label: 'Executive Movement', target: 'Flight tracking for [PERSON/COMPANY]', cost: 250 },
  { label: 'Patent/Filing Watch', target: 'USPTO filings from [COMPANY]', cost: 120 },
  { label: 'Custom OSINT Query', target: '', cost: 200 },
];

export function TaskForce() {
  const { data: agentsData } = useAgents();
  const agents = agentsData?.agents || [];
  const spyAgents = agents.filter((a: any) => a.archetype === 'SPY');
  
  const [missions] = useState<IntelMission[]>(DEMO_MISSIONS);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [targetQuery, setTargetQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (showCreateModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showCreateModal]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-echelon-amber font-bold flex items-center gap-2">
            <Eye className="w-5 h-5" />
            TASK FORCE — INTEL OPS
          </h3>
          <p className="text-terminal-muted text-xs mt-1">
            Deploy Spy agents for custom intelligence gathering
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-echelon-amber/20 border border-echelon-amber/50 text-echelon-amber rounded hover:bg-echelon-amber/30 transition-colors flex items-center gap-2"
        >
          <Target className="w-4 h-4" />
          NEW MISSION
        </button>
      </div>

      {/* Available Spies */}
      <div className="bg-[#0a0a0a] border border-[#1a3a1a] rounded-lg p-4">
        <div className="text-xs text-terminal-muted mb-3">AVAILABLE SPY AGENTS</div>
        <div className="flex gap-3 flex-wrap">
          {spyAgents.length > 0 ? spyAgents.map((spy: any) => (
            <div 
              key={spy.id}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded border',
                (spy.sanity || 75) > 40 
                  ? 'bg-echelon-amber/20 border-echelon-amber/30 text-echelon-amber'
                  : 'bg-echelon-red/20 border-echelon-red/30 text-echelon-red'
              )}
            >
              <span>🕵️</span>
              <span className="font-bold">{spy.name}</span>
              <span className="text-xs opacity-70">
                ({(spy.sanity || 75)}% sanity)
              </span>
            </div>
          )) : (
            <>
              <div className="flex items-center gap-2 px-3 py-2 rounded border bg-echelon-amber/20 border-echelon-amber/30 text-echelon-amber">
                <span>🕵️</span>
                <span className="font-bold">CARDINAL</span>
                <span className="text-xs opacity-70">(72% sanity)</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 rounded border bg-echelon-amber/20 border-echelon-amber/30 text-echelon-amber">
                <span>🕵️</span>
                <span className="font-bold">ORACLE</span>
                <span className="text-xs opacity-70">(85% sanity)</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Active Missions */}
      <div>
        <div className="text-xs text-terminal-muted mb-3">ACTIVE MISSIONS</div>
        
        {missions.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-terminal-border rounded-lg">
            <Eye className="w-10 h-10 mx-auto mb-3 text-terminal-muted" />
            <p className="text-terminal-muted">No active intel missions</p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="text-echelon-amber text-sm hover:underline mt-2"
            >
              Deploy your first spy →
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {missions.map(mission => (
              <div 
                key={mission.id}
                className={clsx(
                  'bg-[#0D0D0D] border rounded-lg p-4',
                  mission.status === 'active' && 'border-echelon-amber/30',
                  mission.status === 'complete' && 'border-echelon-green/30',
                  mission.status === 'failed' && 'border-echelon-red/30',
                  mission.status === 'pending' && 'border-terminal-border'
                )}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-xs font-bold uppercase',
                      mission.status === 'active' && 'bg-echelon-amber/20 text-echelon-amber',
                      mission.status === 'complete' && 'bg-echelon-green/20 text-echelon-green',
                      mission.status === 'failed' && 'bg-echelon-red/20 text-echelon-red',
                      mission.status === 'pending' && 'bg-terminal-bg text-terminal-muted'
                    )}>
                      {mission.status === 'active' && '● '}
                      {mission.status}
                    </span>
                    <span className="text-terminal-muted text-xs">
                      Agent: <span className="text-echelon-amber font-bold">{mission.agent}</span>
                    </span>
                  </div>
                  <span className="text-terminal-muted text-xs flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(mission.createdAt).toLocaleTimeString()}
                  </span>
                </div>
                
                <p className="text-terminal-text text-sm mb-2">
                  <span className="text-terminal-muted">Target:</span> {mission.target}
                </p>
                
                <div className="flex items-center gap-2 text-xs text-terminal-muted">
                  <Coins className="w-3 h-3" />
                  <span>{mission.cost} $ECHELON</span>
                </div>
                
                {mission.results && (
                  <div className="mt-3 p-3 bg-echelon-green/20 border border-echelon-green/30 rounded text-sm text-echelon-green">
                    <span className="font-bold">📡 INTEL RECEIVED:</span>
                    <p className="mt-1 text-terminal-text">{mission.results}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Mission Modal */}
      {showCreateModal && (
        <>
          <div
            className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990]"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="fixed inset-0 z-[9995] flex items-center justify-center p-4 pointer-events-none">
            <div
              className="relative bg-[#0D0D0D] border border-echelon-amber/50 rounded-lg p-4 sm:p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
            <button 
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 text-terminal-muted hover:text-terminal-text"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-echelon-amber/20 rounded-full flex items-center justify-center">
                <Eye className="w-6 h-6 text-echelon-amber" />
              </div>
              <div>
                <h3 className="text-echelon-amber font-bold text-lg">NEW INTEL MISSION</h3>
                <p className="text-terminal-muted text-xs">Task a Spy agent with custom OSINT gathering</p>
              </div>
            </div>
            
            {/* Mission Templates */}
            <div className="mb-4">
              <label className="text-terminal-muted text-sm block mb-2">Mission Type</label>
              <div className="grid grid-cols-2 gap-2">
                {MISSION_TEMPLATES.map((template, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setSelectedTemplate(i);
                      setTargetQuery(template.target);
                    }}
                    className={clsx(
                      'p-2 rounded border text-left text-sm transition-colors',
                      selectedTemplate === i
                        ? 'bg-echelon-amber/20 border-echelon-amber/50 text-echelon-amber'
                        : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:border-echelon-amber/30'
                    )}
                  >
                    <div className="font-bold text-xs">{template.label}</div>
                    <div className="text-xs opacity-70">{template.cost} $ECHELON</div>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Target Query */}
            <div className="mb-4">
              <label className="text-terminal-muted text-sm block mb-2">Target Query</label>
              <textarea
                value={targetQuery}
                onChange={(e) => setTargetQuery(e.target.value)}
                placeholder="e.g., AIS signals for tanker HORIZON near Venezuela"
                rows={3}
                className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-terminal-text focus:border-echelon-amber outline-none resize-none text-sm"
              />
            </div>
            
            {/* Select Agent */}
            <div className="mb-6">
              <label className="text-terminal-muted text-sm block mb-2">Deploy Agent</label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-terminal-text focus:border-echelon-amber outline-none"
              >
                <option value="">Select a Spy agent...</option>
                <option value="CARDINAL">🕵️ CARDINAL (72% sanity)</option>
                <option value="ORACLE">🕵️ ORACLE (85% sanity)</option>
              </select>
            </div>
            
            {/* Cost Summary */}
            <div className="bg-terminal-bg rounded p-3 mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-terminal-muted">Mission Cost</span>
                <span className="text-echelon-amber font-bold">
                  {selectedTemplate !== null ? MISSION_TEMPLATES[selectedTemplate].cost : 200} $ECHELON
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-terminal-muted">Agent Sanity Cost</span>
                <span className="text-echelon-purple">-5 Sanity</span>
              </div>
            </div>
            
            {/* Locked Warning */}
            <div className="bg-echelon-amber/20 border border-echelon-amber/30 rounded p-3 mb-6">
              <div className="flex items-start gap-2">
                <Lock className="w-4 h-4 text-echelon-amber mt-0.5" />
                <div>
                  <p className="text-echelon-amber text-sm font-bold">Wallet Connection Required</p>
                  <p className="text-terminal-muted text-xs mt-1">
                    Intel missions require $ECHELON tokens. Available in full release.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex gap-3">
              <button 
                disabled
                className="flex-1 px-4 py-3 bg-echelon-amber/20 border border-echelon-amber/30 text-echelon-amber/50 rounded cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                DEPLOY MISSION
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-3 bg-terminal-bg border border-terminal-border text-terminal-muted rounded hover:bg-terminal-panel transition-colors"
              >
                CANCEL
              </button>
            </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default TaskForce;

