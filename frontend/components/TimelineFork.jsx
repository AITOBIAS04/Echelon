"use client";

import { useState, useEffect, useCallback } from "react";
import toast from "react-hot-toast";
import { ENDPOINTS, postRequest } from "@/utils/api";
import { GitBranch, Camera, RefreshCw, AlertCircle } from "lucide-react";

const TIMELINE_COLORS = [
  { bg: "bg-blue-500", border: "border-blue-500", text: "text-blue-400" },
  { bg: "bg-purple-500", border: "border-purple-500", text: "text-purple-400" },
  { bg: "bg-pink-500", border: "border-pink-500", text: "text-pink-400" },
  { bg: "bg-orange-500", border: "border-orange-500", text: "text-orange-400" },
  { bg: "bg-cyan-500", border: "border-cyan-500", text: "text-cyan-400" },
];

// --- INTERNAL COMPONENTS ---

function ActionModal({ isOpen, onClose, onSubmit, title, fields, isSubmitting }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-600 rounded-xl p-6 max-w-md w-full shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
        <h3 className="text-xl font-bold text-white mb-6 font-mono">{title}</h3>
        <form onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.target);
          const data = {};
          fields.forEach(f => data[f.name] = formData.get(f.name));
          onSubmit(data);
        }}>
          {fields.map(f => (
            <div key={f.name} className="mb-4">
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1 font-bold">{f.label}</label>
              <input 
                name={f.name} 
                required={f.required} 
                placeholder={f.placeholder} 
                autoFocus={f.focus}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono text-sm" 
              />
            </div>
          ))}
          <div className="flex justify-end gap-3 mt-8">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white text-sm transition-colors">Cancel</button>
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 disabled:text-gray-400 text-white rounded-lg text-sm font-bold transition-all flex items-center gap-2"
            >
              {isSubmitting ? <span className="animate-spin">⚙️</span> : "EXECUTE"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TimelineComparison({ realityId, simulationId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!realityId || !simulationId) return;
    setLoading(true);
    // Use the helper from api.js if possible, or fetch directly
    fetch(ENDPOINTS.TIMELINE_COMPARE(simulationId, realityId))
      .then(res => res.json())
      .then(setData)
      .catch(() => toast.error("Failed to load divergence data"))
      .finally(() => setLoading(false));
  }, [realityId, simulationId]);

  if (loading) return <div className="p-8 text-center text-gray-500 animate-pulse font-mono text-xs">CALCULATING CAUSALITY DRIFT...</div>;
  if (!data || !data.divergence_metrics) return null;

  return (
    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50 mt-4 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-purple-500/50" />
      <h3 className="text-xs font-bold text-purple-400 mb-4 uppercase tracking-widest flex items-center gap-2">
        <GitBranch size={14} /> Divergence Analysis
      </h3>
      <div className="space-y-3">
        {data.divergence_metrics.map((row, i) => (
          <div key={i} className="flex justify-between items-center text-sm border-b border-gray-800 pb-2 last:border-0 last:pb-0">
            <span className="text-gray-400">{row.metric}</span>
            <div className="text-right">
              <div className="text-gray-500 text-xs">Reality: {row.timeline_b}</div>
              <div className="text-white font-mono">Sim: <span className="text-purple-300">{row.timeline_a}</span></div>
              <div className={`text-xs font-bold mt-0.5 ${row.delta.includes('+') ? 'text-green-400' : 'text-red-400'}`}>
                Δ {row.delta}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- MAIN COMPONENT ---

export default function TimelineForkVisualization() {
  const [timelines, setTimelines] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [modalConfig, setModalConfig] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchTimelines = useCallback(async () => {
    try {
      const res = await fetch(ENDPOINTS.TIMELINES);
      const data = await res.json();
      if (data.timelines) {
        setTimelines(data.timelines);
      }
    } catch (e) {
      toast.error("Neural Link Offline: Could not fetch timelines");
    }
  }, []);

  useEffect(() => { fetchTimelines(); }, [fetchTimelines]);

  // NEW: Filter for "My" Timelines (Mock logic for now)
  // In a real app, you'd filter by user_id from the backend
  const masterTimeline = timelines.find(t => t.status === 'master') || { id: "REALITY", label: "Master Reality", created_at: new Date().toISOString() };
  const myForks = timelines.filter(t => t.status === 'active' || t.status === 'completed');

  const handleAction = async (formData) => {
    setIsSubmitting(true);
    const isSnapshot = modalConfig.type === 'snapshot';
    const loadingToast = toast.loading(isSnapshot ? 'Capturing Reality State...' : 'Branching Timeline...');
    
    try {
      if (isSnapshot) {
        await postRequest(ENDPOINTS.TIMELINE_SNAPSHOT + `?label=${encodeURIComponent(formData.label)}`);
        toast.success("Snapshot Secured", { id: loadingToast });
      } else {
        // Fork logic - use selectedNode or fallback to masterTimeline
        const sourceTimeline = selectedNode || masterTimeline;
        const params = new URLSearchParams({
          source_id: sourceTimeline.id,
          fork_name: formData.name,
          reason: formData.reason
        });
        await postRequest(`${ENDPOINTS.TIMELINE_FORK}?${params}`);
        toast.success("Reality Forked Successfully", { id: loadingToast });
      }
      await fetchTimelines();
      setModalConfig(null);
    } catch (err) {
      toast.error(err.message || "Operation Failed", { id: loadingToast });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Toolbar */}
      <div className="bg-gray-800/50 p-4 border-b border-gray-800 flex justify-between items-center rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <GitBranch className="text-blue-400" size={20} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white leading-tight">Quantum Viewer</h2>
            <p className="text-xs text-gray-500 font-mono">{timelines.length} Active Threads</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button onClick={fetchTimelines} className="p-2 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors">
            <RefreshCw size={18} />
          </button>
          <button 
            onClick={() => setModalConfig({ 
              type: 'snapshot', 
              title: 'Capture Reality Snapshot', 
              fields: [{name: 'label', label: 'Snapshot Label', placeholder: 'PRE_EARNINGS_Q1', focus: true, required: true}] 
            })}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
          >
            <Camera size={14} /> Snapshot
          </button>
          <button 
            onClick={() => {
              const sourceTimeline = selectedNode || masterTimeline;
              setModalConfig({ 
                type: 'fork', 
                title: `Fork: ${sourceTimeline.label || 'Master Reality'}`, 
                fields: [
                  {name: 'name', label: 'Fork Name', placeholder: 'BULL_CASE', focus: true, required: true},
                  {name: 'reason', label: 'Divergence Logic', placeholder: 'What if earnings beat expectations?', required: true}
                ] 
              });
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20"
          >
            <GitBranch size={14} /> Fork Reality
          </button>
        </div>
      </div>

      {/* 1. The Master Reality (Always Visible) */}
      <div className="bg-gray-900 rounded-xl p-6 border-l-4 border-gray-500 shadow-lg relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-white/5 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]" />
        <div className="relative flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-gray-500 animate-pulse"/>
              MASTER REALITY
            </h2>
            <p className="text-gray-400 text-sm mt-1">Live feed from NewsAPI, GNews, SportRadar</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono text-white">LIVE</div>
            <div className="text-xs text-gray-500">Last Sync: Just now</div>
          </div>
        </div>
      </div>

      {/* 2. My Active Simulations (The Forks) */}
      <h3 className="text-lg font-bold text-white px-2">MY ACTIVE SIMULATIONS</h3>
      
      <div className="grid gap-4">
        {myForks.map(fork => (
          <div key={fork.id} className="bg-gray-900/80 rounded-xl p-6 border-l-4 border-purple-500 shadow-lg relative group hover:bg-gray-800 transition-all">
            {/* Connector Line (Visual trick) */}
            <div className="absolute -top-8 left-6 w-0.5 h-8 bg-gradient-to-b from-gray-500 to-purple-500 -z-10" />
            
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-lg font-bold text-purple-400 flex items-center gap-2">
                   <span className="w-2 h-2 rounded-full bg-purple-500"/>
                   {fork.label || fork.id}
                </h4>
                <p className="text-gray-300 text-sm mt-1 italic">"{fork.fork_reason || 'No reason specified'}"</p>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={() => setSelectedNode(fork)}
                  className="px-3 py-1 bg-purple-900/50 text-purple-300 text-xs rounded border border-purple-500/30 hover:bg-purple-900 transition-colors"
                >
                  View Divergence
                </button>
              </div>
            </div>

            {/* Quick Stats Row */}
            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-800">
              <div>
                <div className="text-xs text-gray-500 uppercase">Status</div>
                <div className="text-green-400 text-sm font-bold">{fork.status?.toUpperCase() || 'UNKNOWN'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase">Created</div>
                <div className="text-gray-300 text-sm">{new Date(fork.created_at).toLocaleDateString()}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase">Agent</div>
                <div className="text-gray-300 text-sm">Active</div>
              </div>
            </div>
          </div>
        ))}

        {myForks.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed border-gray-800 rounded-xl text-gray-500">
            <p>No active simulations.</p>
            <button 
              onClick={() => setModalConfig({ 
                type: 'fork', 
                title: `Fork: ${masterTimeline.label}`, 
                fields: [
                  {name: 'name', label: 'Fork Name', placeholder: 'BULL_CASE', focus: true, required: true},
                  {name: 'reason', label: 'Divergence Logic', placeholder: 'What if earnings beat expectations?', required: true}
                ] 
              })}
              className="mt-2 text-purple-400 hover:underline"
            >
              Create a new Fork
            </button>
          </div>
        )}
      </div>

      {/* Details Panel (Modal/Overlay) */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-2xl w-full shadow-2xl border border-gray-700 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedNode.label || selectedNode.id}</h2>
                <div className="text-xs font-mono text-gray-600 mt-1 select-all">{selectedNode.id}</div>
              </div>
              <button 
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4 mb-8">
              <div className="flex justify-between text-sm border-b border-gray-800 pb-2">
                <span className="text-gray-400">Status</span>
                <span className="text-white capitalize">{selectedNode.status}</span>
              </div>
              <div className="flex justify-between text-sm border-b border-gray-800 pb-2">
                <span className="text-gray-400">Created</span>
                <span className="text-white">{new Date(selectedNode.created_at).toLocaleDateString()}</span>
              </div>
              {selectedNode.fork_reason && (
                <div className="bg-blue-900/20 p-3 rounded border border-blue-800/50 text-sm">
                  <div className="text-blue-400 text-xs font-bold mb-1 uppercase">Fork Logic</div>
                  <div className="text-blue-100 leading-relaxed">{selectedNode.fork_reason}</div>
                </div>
              )}
            </div>
            
            {selectedNode.parent_id && (
              <TimelineComparison 
                realityId={selectedNode.parent_id} 
                simulationId={selectedNode.id} 
              />
            )}
            {selectedNode.status === 'active' && (
              <button className="w-full mt-6 bg-green-600 hover:bg-green-500 text-white py-3 rounded-lg font-bold text-sm shadow-lg shadow-green-900/20 transition-all">
                ENTER SIMULATION
              </button>
            )}
          </div>
        </div>
      )}

      <ActionModal 
        isOpen={!!modalConfig} 
        onClose={() => setModalConfig(null)} 
        onSubmit={handleAction}
        isSubmitting={isSubmitting}
        {...modalConfig}
      />
    </div>
  );
}
