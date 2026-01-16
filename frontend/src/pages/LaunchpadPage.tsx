import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Clock, ArrowLeft } from 'lucide-react';
import { listLaunches } from '../api/launchpad';
import { LaunchCardMini } from '../components/home/LaunchCardMini';
import { getHomePreference } from '../lib/userPrefs';
import type { LaunchPhase, LaunchCard } from '../types/launchpad';

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
