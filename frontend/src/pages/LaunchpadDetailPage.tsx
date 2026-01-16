import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ExternalLink, Play, Database, GitBranch } from 'lucide-react';
import { listLaunches } from '../api/launchpad';
import { ReplayDrawer } from '../components/replay/ReplayDrawer';
import type { LaunchCard } from '../types/launchpad';
import type { ReplayPointer } from '../types/replay';

/**
 * Get phase badge color and label
 */
function getPhaseBadge(phase: LaunchCard['phase']): { bg: string; text: string; label: string } {
  switch (phase) {
    case 'draft':
      return { bg: '#666666', text: '#FFFFFF', label: 'DRAFT' };
    case 'sandbox':
      return { bg: '#FF9500', text: '#FFFFFF', label: 'SANDBOX' };
    case 'pilot':
      return { bg: '#00D4FF', text: '#000000', label: 'PILOT' };
    case 'graduated':
      return { bg: '#00FF41', text: '#000000', label: 'GRADUATED' };
    case 'failed':
      return { bg: '#FF3B3B', text: '#FFFFFF', label: 'FAILED' };
  }
}

/**
 * Get category badge color
 */
function getCategoryColor(category: LaunchCard['category']): string {
  switch (category) {
    case 'theatre':
      return '#00D4FF';
    case 'osint':
      return '#9932CC';
  }
}

/**
 * Get quality score color
 */
function getQualityColor(score: number): string {
  if (score >= 80) return '#00FF41'; // green
  if (score >= 60) return '#FF9500'; // amber
  return '#FF3B3B'; // red
}

/**
 * Mock mapping of launch IDs to timeline IDs
 * In production, this would come from the API
 */
const launchToTimelineMap: Record<string, string> = {
  'launch_grad_001': 'tl_neon_courier_001',
  'launch_grad_002': 'tl_disaster_response_001',
  'launch_grad_003': 'tl_sentiment_tracking_001',
};

/**
 * LaunchpadDetailPage Component
 * 
 * Displays detailed information about a single launch card.
 */
export function LaunchpadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [launch, setLaunch] = useState<LaunchCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replayOpen, setReplayOpen] = useState(false);
  const [replayPointer, setReplayPointer] = useState<ReplayPointer | null>(null);

  useEffect(() => {
    const fetchLaunch = async () => {
      if (!id) {
        setError('Launch ID is required');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // Check localStorage drafts first
        let found: LaunchCard | undefined;
        try {
          const stored = localStorage.getItem('launchpad_drafts');
          if (stored) {
            const drafts: LaunchCard[] = JSON.parse(stored);
            found = drafts.find((l) => l.id === id);
          }
        } catch {
          // Ignore localStorage errors
        }
        
        // If not found in localStorage, check API
        if (!found) {
          const allLaunches = await listLaunches();
          found = allLaunches.find((l) => l.id === id);
        }
        
        if (!found) {
          setError('Launch not found');
          setLaunch(null);
        } else {
          setLaunch(found);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch launch';
        setError(errorMessage);
        setLaunch(null);
      } finally {
        setLoading(false);
      }
    };

    fetchLaunch();
  }, [id]);

  const handleOpenMarket = () => {
    if (!launch) return;
    
    // Check if launch is graduated and has a timeline mapping
    if (launch.phase === 'graduated') {
      const timelineId = launchToTimelineMap[launch.id];
      if (timelineId) {
        navigate(`/timeline/${timelineId}`);
      }
    }
  };

  const handleViewReplay = () => {
    if (!launch) return;
    
    // Mock pointer - in production, would fetch actual latest fork ID
    const pointer: ReplayPointer = {
      timelineId: launchToTimelineMap[launch.id] || `tl_${launch.id}`,
      forkId: 'latest',
    };
    setReplayPointer(pointer);
    setReplayOpen(true);
  };

  const handleCloseReplay = () => {
    setReplayOpen(false);
    setReplayPointer(null);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-muted animate-pulse">Loading launch details...</div>
      </div>
    );
  }

  if (error || !launch) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-lg font-semibold text-terminal-text mb-2">
          {error || 'Launch not found'}
        </p>
        <button
          onClick={() => navigate('/launchpad')}
          className="px-4 py-2 bg-terminal-bg border border-terminal-border rounded hover:border-echelon-cyan transition text-sm mt-4"
        >
          Back to Launchpad
        </button>
      </div>
    );
  }

  const phaseBadge = getPhaseBadge(launch.phase);
  const categoryColor = getCategoryColor(launch.category);
  const qualityColor = getQualityColor(launch.qualityScore);
  const canOpenMarket = launch.phase === 'graduated' && launchToTimelineMap[launch.id];

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
      {/* Header */}
      <div className="flex items-start justify-between flex-shrink-0">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <span
              className="text-xs font-bold px-3 py-1 rounded"
              style={{
                backgroundColor: phaseBadge.bg,
                color: phaseBadge.text,
              }}
            >
              {phaseBadge.label}
            </span>
            <span
              className="text-xs px-3 py-1 rounded border"
              style={{
                borderColor: categoryColor,
                color: categoryColor,
                backgroundColor: `${categoryColor}10`,
              }}
            >
              {launch.category.toUpperCase()}
            </span>
            {launch.exportEligible && (
              <span className="flex items-center gap-1 text-xs text-[#00D4FF]">
                <Database className="w-3 h-3" />
                EXPORT ELIGIBLE
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold text-terminal-text uppercase tracking-wide mb-2">
            {launch.title}
          </h1>
          {launch.shortDescription && (
            <p className="text-sm text-terminal-muted mt-2">{launch.shortDescription}</p>
          )}
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Quality Score */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <h3 className="text-xs font-semibold text-terminal-muted uppercase tracking-wide mb-3">
            Quality Score
          </h3>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl font-mono font-bold" style={{ color: qualityColor }}>
              {launch.qualityScore}
            </span>
            <span className="text-sm text-terminal-muted">/ 100</span>
          </div>
          <div className="w-full h-2 bg-[#1A1A1A] rounded-full overflow-hidden">
            <div
              className="h-full transition-all"
              style={{
                width: `${launch.qualityScore}%`,
                backgroundColor: qualityColor,
              }}
            />
          </div>
        </div>

        {/* Fork Target Range */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <h3 className="text-xs font-semibold text-terminal-muted uppercase tracking-wide mb-3 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Fork Target Range
          </h3>
          <div className="text-2xl font-mono font-bold text-terminal-text">
            {launch.forkTargetRange[0]} - {launch.forkTargetRange[1]}
          </div>
          <p className="text-xs text-terminal-muted mt-2">Expected forks per episode</p>
        </div>

        {/* Episode Length */}
        {launch.episodeLengthSec && (
          <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
            <h3 className="text-xs font-semibold text-terminal-muted uppercase tracking-wide mb-3">
              Episode Length
            </h3>
            <div className="text-2xl font-mono font-bold text-terminal-text">
              {launch.episodeLengthSec}s
            </div>
          </div>
        )}

        {/* Tags */}
        <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
          <h3 className="text-xs font-semibold text-terminal-muted uppercase tracking-wide mb-3">
            Tags
          </h3>
          <div className="flex flex-wrap gap-2">
            {launch.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 text-xs bg-terminal-bg border border-terminal-border rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-terminal-muted">Created:</span>{' '}
            <span className="text-terminal-text font-mono">
              {new Date(launch.createdAt).toLocaleDateString()}
            </span>
          </div>
          <div>
            <span className="text-terminal-muted">Updated:</span>{' '}
            <span className="text-terminal-text font-mono">
              {new Date(launch.updatedAt).toLocaleDateString()}
            </span>
          </div>
          {launch.founderId && (
            <div>
              <span className="text-terminal-muted">Founder:</span>{' '}
              <span className="text-terminal-text font-mono">{launch.founderId}</span>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4 flex-shrink-0 pb-4">
        <button
          onClick={handleOpenMarket}
          disabled={!canOpenMarket}
          className={`flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded transition ${
            canOpenMarket
              ? 'bg-[#00D4FF]/20 border border-[#00D4FF] text-[#00D4FF] hover:bg-[#00D4FF]/30'
              : 'bg-terminal-bg border border-terminal-border text-terminal-muted cursor-not-allowed'
          }`}
        >
          <ExternalLink className="w-4 h-4" />
          OPEN MARKET
        </button>
        <button
          onClick={handleViewReplay}
          className="flex items-center gap-2 px-6 py-3 text-sm font-semibold bg-terminal-bg border border-terminal-border rounded hover:border-[#00D4FF] hover:text-[#00D4FF] transition"
        >
          <Play className="w-4 h-4" />
          VIEW REPLAY
        </button>
      </div>

      {/* Replay Drawer */}
      <ReplayDrawer
        open={replayOpen}
        onClose={handleCloseReplay}
        pointer={replayPointer}
      />
    </div>
  );
}
