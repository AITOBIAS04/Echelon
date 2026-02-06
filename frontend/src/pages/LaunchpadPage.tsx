import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Clock, Rocket, Flame, AlertTriangle, Shield, Copy, SlidersHorizontal, ArrowRight } from 'lucide-react';
import { listLaunches } from '../api/launchpad';
import { LaunchCardMini } from '../components/home/LaunchCardMini';
import type { LaunchPhase, LaunchCard } from '../types/launchpad';
import { useDemoEnabled, useDemoLaunchFeed } from '../demo/hooks';
import { demoStore } from '../demo/demoStore';

type SortMode = 'trending' | 'new';

/**
 * LaunchpadPage Component
 * 
 * Main launchpad feed page with tabs for different phases
 * and sort toggle (Trending vs New).
 */
export function LaunchpadPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<LaunchPhase | 'drafts'>('sandbox');
  const [sortMode, setSortMode] = useState<SortMode>('trending');
  const [launches, setLaunches] = useState<LaunchCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Demo hooks
  const demoEnabled = useDemoEnabled();
  const liveFeed = useDemoLaunchFeed();

  // Fetch launches based on active tab
  useEffect(() => {
    const fetchLaunches = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (activeTab === 'drafts') {
          // For drafts, filter from all launches
          const allLaunches = await listLaunches();
          const drafts = allLaunches.filter((l) => l.phase === 'draft');
          setLaunches(drafts);
        } else {
          const filtered = await listLaunches(activeTab as LaunchPhase);
          setLaunches(filtered);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch launches';
        setError(errorMessage);
        setLaunches([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLaunches();
  }, [activeTab]);

  // Sort launches based on sort mode
  const sortedLaunches = useMemo(() => {
    if (sortMode === 'trending') {
      // Sort by qualityScore descending
      return [...launches].sort((a, b) => b.qualityScore - a.qualityScore);
    } else {
      // Sort by createdAt descending (newest first)
      return [...launches].sort((a, b) => {
        const dateA = new Date(a.createdAt).getTime();
        const dateB = new Date(b.createdAt).getTime();
        return dateB - dateA;
      });
    }
  }, [launches, sortMode]);

  const tabs: Array<{ id: LaunchPhase | 'drafts'; label: string }> = [
    { id: 'sandbox', label: 'Sandbox' },
    { id: 'pilot', label: 'Pilot' },
    { id: 'graduated', label: 'Graduated' },
    { id: 'drafts', label: 'My Drafts' },
  ];

  return (
    <div className="h-full flex flex-col gap-4 p-4">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-xl border border-terminal-border bg-gradient-to-r from-terminal-panel via-echelon-cyan/[0.03] to-terminal-panel p-5 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-2.5 h-2.5 rounded-full bg-echelon-cyan animate-pulse-slow shadow-glow-cyan" />
            <div>
              <h1 className="page-title">Launch Terminal</h1>
              <p className="text-xs text-terminal-text-muted mt-1">Deploy, monitor, and scale prediction timelines</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="data-label">Active</span>
              <span className="data-value text-sm">{sortedLaunches.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="data-label">Feed</span>
              <span className="data-value text-sm">{demoEnabled ? liveFeed.length : 0}</span>
            </div>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-echelon-cyan/20 to-transparent" />
      </div>

      {/* Live launches feed */}
      <div className="terminal-panel p-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Rocket className="w-4 h-4 text-status-entropy" />
            <span className="section-title-accented">Live Launches</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-terminal-border bg-terminal-card text-terminal-text-muted">
              {demoEnabled ? "Live feed" : "Preview"}
            </span>
          </div>
        </div>

        <div className="max-h-[180px] overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent space-y-2 pr-1">
          {(demoEnabled ? liveFeed : []).slice(0, 10).map((it: any) => {
            const icon =
              it.kind === "launch" ? <Rocket className="w-4 h-4 text-status-success" /> :
              it.kind === "milestone" ? <Flame className="w-4 h-4 text-status-info" /> :
              <AlertTriangle className="w-4 h-4 text-status-danger" />;

            const accent =
              it.accent === "success" ? "border-l-status-success" :
              it.accent === "warning" ? "border-l-status-warning" :
              it.accent === "danger" ? "border-l-status-danger" :
              "border-l-status-info";

            return (
              <div key={it.id} className={`flex items-center gap-3 bg-terminal-card border border-terminal-border rounded-lg p-3 border-l-4 ${accent}`}>
                {icon}
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-terminal-text">{it.actor}</div>
                  <div className="text-xs text-terminal-text-secondary truncate">{it.message}</div>
                </div>
                {it.cta?.action === "inject_shield" ? (
                  <button
                    onClick={() => {
                      demoStore.pushToast("Shield injected", "Stability intervention queued");
                    }}
                    className="btn-ghost gap-1"
                  >
                    <Shield className="w-3.5 h-3.5" />
                    {it.cta.label}
                  </button>
                ) : (
                  <span className="text-[10px] text-terminal-text-muted tabular-nums">
                    {new Date(it.ts).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
            );
          })}

          {!demoEnabled ? (
            <div className="text-xs text-terminal-text-muted py-2">
              Enable demo mode to activate the live feed.
            </div>
          ) : liveFeed.length === 0 ? (
            <div className="text-xs text-terminal-text-muted py-2">
              Feed initialising...
            </div>
          ) : null}
        </div>
      </div>

      {/* Quick Launch CTA */}
      <div className="terminal-card overflow-hidden flex-shrink-0">
        <div className="px-4 py-3 border-b border-terminal-border">
          <span className="section-title">Quick Launch</span>
        </div>

        {sortedLaunches.length > 0 ? (
          <button
            onClick={() => {
              demoStore.pushToast("Fork cloned", "Draft created in Launchpad");
              navigate('/launchpad/new');
            }}
            className="w-full group flex items-center justify-between p-4 hover:bg-terminal-elevated transition-all text-left hover-lift"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-status-entropy/10 border border-status-entropy/20 flex items-center justify-center">
                <Copy className="w-5 h-5 text-status-entropy" />
              </div>
              <div>
                <div className="text-sm font-semibold text-terminal-text">Clone & configure</div>
                <div className="text-xs text-terminal-text-muted mt-0.5">
                  Fast path using top performer: {sortedLaunches[0].title}
                </div>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-terminal-text-muted group-hover:text-status-entropy transition-colors" />
          </button>
        ) : (
          <div className="p-4 text-xs text-terminal-text-muted">No candidate forks available.</div>
        )}

        <div className="h-px bg-terminal-border" />

        <button
          onClick={() => navigate('/launchpad/new')}
          className="w-full group flex items-center justify-between p-4 hover:bg-terminal-elevated transition-all text-left hover-lift"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-status-info/10 border border-status-info/20 flex items-center justify-center">
              <SlidersHorizontal className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <div className="text-sm font-semibold text-terminal-text">Open advanced</div>
              <div className="text-xs text-terminal-text-muted mt-0.5">
                Define risk, oracle composition, and fork parameters
              </div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-terminal-text-muted group-hover:text-status-info transition-colors" />
        </button>
      </div>

      {/* Tabs and Sort Toggle */}
      <div className="flex items-center justify-between flex-shrink-0">
        {/* Phase Tabs */}
        <div className="flex items-center gap-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={isActive ? 'btn-cyan' : 'btn-ghost'}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Sort Toggle */}
        <div className="flex items-center gap-2">
          <span className="data-label">Sort</span>
          <div className="flex items-center gap-1 bg-terminal-bg border border-terminal-border rounded-lg">
            <button
              onClick={() => setSortMode('trending')}
              className={`px-3 py-1.5 text-xs flex items-center gap-1 rounded-l-lg transition-all ${
                sortMode === 'trending'
                  ? 'bg-echelon-cyan/15 text-echelon-cyan'
                  : 'text-terminal-text-muted hover:text-terminal-text'
              }`}
            >
              <TrendingUp className="w-3 h-3" />
              Trending
            </button>
            <div className="w-px h-4 bg-terminal-border" />
            <button
              onClick={() => setSortMode('new')}
              className={`px-3 py-1.5 text-xs flex items-center gap-1 rounded-r-lg transition-all ${
                sortMode === 'new'
                  ? 'bg-echelon-cyan/15 text-echelon-cyan'
                  : 'text-terminal-text-muted hover:text-terminal-text'
              }`}
            >
              <Clock className="w-3 h-3" />
              New
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-terminal-text-muted animate-pulse">Loading launches...</div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-semibold text-terminal-text mb-2">Error loading launches</p>
            <p className="text-sm text-terminal-text-muted">{error}</p>
          </div>
        ) : sortedLaunches.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-semibold text-terminal-text mb-2">No launches found</p>
            <p className="text-sm text-terminal-text-muted">
              {activeTab === 'drafts'
                ? 'You have no drafts yet. Create a new timeline to get started.'
                : `No ${activeTab} launches available.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sortedLaunches.map((launch, idx) => (
              <div key={launch.id} className="animate-stagger-in" style={{ animationDelay: `${idx * 40}ms` }}>
                <LaunchCardMini launch={launch} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
