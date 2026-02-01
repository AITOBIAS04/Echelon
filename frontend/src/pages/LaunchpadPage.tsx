import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Clock, ArrowLeft, Rocket, Flame, AlertTriangle, Shield } from 'lucide-react';
import { listLaunches } from '../api/launchpad';
import { LaunchCardMini } from '../components/home/LaunchCardMini';
import { getHomePreference } from '../lib/userPrefs';
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
  
  const homePref = getHomePreference();
  const showGoToMarkets = homePref === 'launchpad';

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
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          {showGoToMarkets && (
            <button
              onClick={() => navigate('/home')}
              className="flex items-center gap-2 px-3 py-1.5 text-xs bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] hover:text-[#00D4FF] transition"
              title="Go to Markets"
            >
              <ArrowLeft className="w-3 h-3" />
              Go to Markets
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide">
              Launchpad
            </h1>
            <p className="text-sm text-terminal-muted mt-1">
              Discover and launch new timeline markets
            </p>
          </div>
        </div>
      </div>

      {/* Live launches feed */}
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Rocket className="w-4 h-4 text-status-entropy" />
            <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Live Launches</h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-terminal-border bg-terminal-card text-terminal-text-muted">
              {demoEnabled ? "Live feed" : "Preview"}
            </span>
          </div>
        </div>

        <div className="max-h-[220px] overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent space-y-2 pr-1">
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
                    className="px-2.5 py-1.5 text-xs rounded border border-terminal-border hover:border-status-entropy/60 hover:text-status-entropy transition flex items-center gap-1"
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

      {/* Clone CTA */}
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-terminal-text uppercase tracking-wide">Clone top yielding fork</h3>
            <p className="text-xs text-terminal-text-secondary mt-1">
              Fast path to launch. Clones inherit baseline parameters and require active management.
            </p>
          </div>
        </div>

        {sortedLaunches.length > 0 ? (
          <div className="bg-terminal-card border border-terminal-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <div className="text-base font-semibold text-terminal-text truncate">{sortedLaunches[0].title}</div>
                <div className="text-xs text-terminal-text-secondary mt-1">
                  Quality score: <span className="text-terminal-text tabular-nums">{sortedLaunches[0].qualityScore}</span>
                  {" "}•{" "}
                  Estimated yield:{" "}
                  <span className="text-terminal-text tabular-nums">
                    ${Math.max(40, Math.floor(sortedLaunches[0].qualityScore * 6))}/hour
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  demoStore.pushToast("Fork cloned", "Draft created in Launchpad");
                  navigate('/launchpad/new');
                }}
                className="px-4 py-2 rounded-md font-semibold text-sm border border-status-entropy/40 bg-status-entropy/10 hover:bg-status-entropy/15 text-terminal-text transition"
              >
                Clone & configure
              </button>
            </div>
          </div>
        ) : (
          <div className="text-xs text-terminal-text-muted">No candidate forks available.</div>
        )}
      </div>

      {/* Create from scratch (Advanced) */}
      <details className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <summary className="cursor-pointer select-none text-sm font-semibold text-terminal-text uppercase tracking-wide">
          Create from scratch (Advanced)
        </summary>
        <div className="mt-3 text-xs text-terminal-text-secondary">
          Use the advanced flow to define risk, oracle composition, and fork parameters.
        </div>
        <div className="mt-3">
          <button
            onClick={() => navigate('/launchpad/new')}
            className="px-4 py-2 text-xs border border-terminal-border rounded hover:border-status-info/60 hover:text-status-info transition"
          >
            Open advanced create
          </button>
        </div>
      </details>

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
                className={`px-4 py-2 text-sm font-medium rounded transition ${
                  isActive
                    ? 'bg-[#00D4FF]/20 border border-[#00D4FF] text-[#00D4FF]'
                    : 'bg-terminal-bg border border-terminal-border text-terminal-muted hover:text-terminal-text'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Sort Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-terminal-muted">Sort:</span>
          <div className="flex items-center gap-1 bg-terminal-bg border border-terminal-border rounded">
            <button
              onClick={() => setSortMode('trending')}
              className={`px-3 py-1.5 text-xs flex items-center gap-1 transition ${
                sortMode === 'trending'
                  ? 'bg-[#00D4FF]/20 text-[#00D4FF]'
                  : 'text-terminal-muted hover:text-terminal-text'
              }`}
            >
              <TrendingUp className="w-3 h-3" />
              Trending
            </button>
            <div className="w-px h-4 bg-terminal-border" />
            <button
              onClick={() => setSortMode('new')}
              className={`px-3 py-1.5 text-xs flex items-center gap-1 transition ${
                sortMode === 'new'
                  ? 'bg-[#00D4FF]/20 text-[#00D4FF]'
                  : 'text-terminal-muted hover:text-terminal-text'
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
            <div className="text-terminal-muted animate-pulse">Loading launches...</div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-semibold text-terminal-text mb-2">Error loading launches</p>
            <p className="text-sm text-terminal-muted">{error}</p>
          </div>
        ) : sortedLaunches.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-semibold text-terminal-text mb-2">No launches found</p>
            <p className="text-sm text-terminal-muted">
              {activeTab === 'drafts'
                ? 'You have no drafts yet. Create a new timeline to get started.'
                : `No ${activeTab} launches available.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sortedLaunches.map((launch) => (
              <LaunchCardMini key={launch.id} launch={launch} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
