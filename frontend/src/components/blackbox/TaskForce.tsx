import { useState } from 'react';
import { Eye, Send, Lock, X, Target, Clock, Coins, Zap } from 'lucide-react';
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <Eye className="w-5 h-5 text-blue-400" />
            Task Force — Intel Ops
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Deploy Spy agents for custom intelligence gathering
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-md hover:bg-blue-500/20 transition-colors flex items-center gap-2 text-sm font-medium"
        >
          <Target className="w-4 h-4" />
          New Mission
        </button>
      </div>

      {/* Available Spies */}
      <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4">
        <div className="text-sm font-medium text-slate-400 mb-3">Available Spy Agents</div>
        <div className="flex gap-3 flex-wrap">
          {spyAgents.length > 0 ? spyAgents.map((spy: any) => (
            <div
              key={spy.id}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-md border',
                (spy.sanity || 75) > 40
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                  : 'bg-red-500/10 border-red-500/30 text-red-400'
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
              <div className="flex items-center gap-2 px-3 py-2 rounded-md border bg-amber-500/10 border-amber-500/30 text-amber-400">
                <span>🕵️</span>
                <span className="font-bold">CARDINAL</span>
                <span className="text-xs opacity-70">(72% sanity)</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 rounded-md border bg-amber-500/10 border-amber-500/30 text-amber-400">
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
        <div className="text-sm font-medium text-slate-400 mb-3">Active Missions</div>

        {missions.length === 0 ? (
          <div className="text-center py-10 bg-slate-900/50 border border-slate-700/50 rounded-lg">
            <Eye className="w-10 h-10 mx-auto mb-3 text-slate-500 opacity-50" />
            <p className="text-slate-400">No active intel missions</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-blue-400 text-sm hover:underline mt-2"
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
                  'bg-slate-900/50 border rounded-lg p-4',
                  mission.status === 'active' && 'border-blue-500/30',
                  mission.status === 'complete' && 'border-emerald-500/30',
                  mission.status === 'failed' && 'border-red-500/30',
                  mission.status === 'pending' && 'border-slate-700/50'
                )}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'px-2 py-0.5 rounded text-xs font-medium uppercase',
                      mission.status === 'active' && 'bg-blue-500/10 text-blue-400',
                      mission.status === 'complete' && 'bg-emerald-500/10 text-emerald-400',
                      mission.status === 'failed' && 'bg-red-500/10 text-red-400',
                      mission.status === 'pending' && 'bg-slate-800/50 text-slate-400'
                    )}>
                      {mission.status === 'active' && '● '}
                      {mission.status}
                    </span>
                    <span className="text-slate-400 text-xs">
                      Agent: <span className="text-amber-400 font-bold">{mission.agent}</span>
                    </span>
                  </div>
                  <span className="text-slate-500 text-xs flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(mission.createdAt).toLocaleTimeString()}
                  </span>
                </div>

                <p className="text-slate-300 text-sm mb-2">
                  <span className="text-slate-500">Target:</span> {mission.target}
                </p>

                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Coins className="w-3.5 h-3.5" />
                  <span>{mission.cost} $ECHELON</span>
                </div>

                {mission.results && (
                  <div className="mt-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-md">
                    <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium mb-1">
                      <Zap className="w-4 h-4" />
                      Intel Received
                    </div>
                    <p className="text-slate-300 text-sm">{mission.results}</p>
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
            className="fixed inset-0 bg-black/90 backdrop-blur-md z-[9990]"
            onClick={() => setShowCreateModal(false)}
          />
          {/* Single scroll container (iOS-friendly) */}
          <div
            className="fixed inset-0 z-[9995] overflow-y-scroll overscroll-contain p-4"
            style={{ WebkitOverflowScrolling: 'touch', touchAction: 'pan-y' }}
          >
            <div className="min-h-full flex items-start justify-center py-8">
              <div
                className="relative bg-slate-900 border border-slate-700 rounded-lg p-4 sm:p-6 max-w-lg w-full"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="absolute top-4 right-4 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-5 h-5" />
                </button>

                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <Eye className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-200">New Intel Mission</h3>
                    <p className="text-sm text-slate-400">Task a Spy agent with custom OSINT gathering</p>
                  </div>
                </div>

                {/* Mission Templates */}
                <div className="mb-4">
                  <label className="text-sm text-slate-400 block mb-2">Mission Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {MISSION_TEMPLATES.map((template, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setSelectedTemplate(i);
                          setTargetQuery(template.target);
                        }}
                        className={clsx(
                          'p-2 rounded-md border text-left text-sm transition-colors',
                          selectedTemplate === i
                            ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                            : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-blue-500/30'
                        )}
                      >
                        <div className="font-medium text-xs">{template.label}</div>
                        <div className="text-xs opacity-70">{template.cost} $ECHELON</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Target Query */}
                <div className="mb-4">
                  <label className="text-sm text-slate-400 block mb-2">Target Query</label>
                  <textarea
                    value={targetQuery}
                    onChange={(e) => setTargetQuery(e.target.value)}
                    placeholder="e.g., AIS signals for tanker HORIZON near Venezuela"
                    rows={3}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-md px-3 py-2 text-slate-200 focus:border-blue-500 outline-none resize-none text-sm"
                  />
                </div>

                {/* Select Agent */}
                <div className="mb-6">
                  <label className="text-sm text-slate-400 block mb-2">Deploy Agent</label>
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-md px-3 py-2 text-slate-200 focus:border-blue-500 outline-none"
                  >
                    <option value="">Select a Spy agent...</option>
                    <option value="CARDINAL">🕵️ CARDINAL (72% sanity)</option>
                    <option value="ORACLE">🕵️ ORACLE (85% sanity)</option>
                  </select>
                </div>

                {/* Cost Summary */}
                <div className="bg-slate-800/50 rounded-md p-3 mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-400">Mission Cost</span>
                    <span className="text-blue-400 font-bold">
                      {selectedTemplate !== null ? MISSION_TEMPLATES[selectedTemplate].cost : 200} $ECHELON
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Agent Sanity Cost</span>
                    <span className="text-purple-400">-5 Sanity</span>
                  </div>
                </div>

                {/* Locked Warning */}
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-md p-3 mb-6">
                  <div className="flex items-start gap-2">
                    <Lock className="w-4 h-4 text-amber-400 mt-0.5" />
                    <div>
                      <p className="text-amber-400 text-sm font-medium">Wallet Connection Required</p>
                      <p className="text-slate-400 text-xs mt-1">
                        Intel missions require $ECHELON tokens. Available in full release.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    disabled
                    className="flex-1 px-4 py-3 bg-blue-500/10 border border-blue-500/30 text-blue-400/50 rounded-md cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Deploy Mission
                  </button>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-3 bg-slate-800/50 border border-slate-700/50 text-slate-400 rounded-md hover:bg-slate-800 hover:border-slate-600/50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default TaskForce;
