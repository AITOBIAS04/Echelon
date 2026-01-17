import { useState, type ReactNode } from 'react';
import { useOpsBoard } from '../../hooks/useOpsBoard';
import { OpsRow } from './OpsRow';
import { BreachesPanel } from './BreachesPanel';
import { computeTrendingScore } from '../../lib/trendingRanker';
import type { OpsCard } from '../../types/opsBoard';

/**
 * OpsBoard Column Props
 */
interface OpsColumnProps {
  title: string;
  accentColor: string;
  cards: OpsCard[];
  emptyMessage: string;
  headerBottom?: ReactNode;
}

/**
 * OpsColumn Component
 * 
 * Individual column in the 3-column grid layout.
 */
function OpsColumn({ title, accentColor, cards, emptyMessage, headerBottom }: OpsColumnProps) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Sticky Header */}
      <div
        className="sticky top-0 z-10 flex flex-col gap-1 px-3 py-2 mb-2 bg-terminal-bg/95 backdrop-blur-sm border-b flex-shrink-0"
        style={{ borderColor: `${accentColor}40` }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: accentColor }}
          />
          <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">
            {title}
          </h3>
          <span className="text-xs text-terminal-muted font-mono ml-auto">
            ({cards.length})
          </span>
        </div>
        {headerBottom}
      </div>

      {/* Cards List - Independent Scroll */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        <div className="flex flex-col pb-2">
          {cards.length === 0 ? (
            <div className="text-terminal-muted text-xs py-8 text-center px-4">
              {emptyMessage}
            </div>
          ) : (
            cards.map((card) => (
              <OpsRow key={card.id} card={card} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * RiskAndResultsColumn Component
 * 
 * Right column showing At Risk on top and Recently Graduated on bottom.
 */
function RiskAndResultsColumn({
  atRisk,
  headerBottom,
}: {
  atRisk: OpsCard[];
  headerBottom?: ReactNode;
}) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* At Risk Section */}
      <div className="flex flex-col flex-1 min-h-0">
        <div
          className="sticky top-0 z-10 flex flex-col gap-1 px-3 py-2 mb-2 bg-terminal-bg/95 backdrop-blur-sm border-b flex-shrink-0"
          style={{ borderColor: '#FF3B3B40' }}
        >
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#FF3B3B' }} />
            <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">At Risk</h3>
            <span className="text-xs text-terminal-muted font-mono ml-auto">({atRisk.length})</span>
          </div>
          {headerBottom}
        </div>
        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <div className="flex flex-col pb-2">
            {atRisk.length === 0 ? (
              <div className="text-terminal-muted text-xs py-4 text-center px-4">
                No risks detected
              </div>
            ) : (
              atRisk.map((card) => (
                <OpsRow key={card.id} card={card} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-terminal-border mx-3 my-2 flex-shrink-0" />

      {/* Breaches Section */}
      <div className="flex flex-col flex-1 min-h-0">
        <BreachesPanel />
      </div>
    </div>
  );
}

/**
 * OpsBoard Component
 * 
 * BullX-style 3-column vertical grid layout.
 * Column 1: New Creations (Green)
 * Column 2: About to Happen (Orange)
 * Column 3: Critical & Graduating (Red/Purple)
 */
/**
 * OpsBoardSkeleton Component
 * 
 * Simple placeholder skeleton for loading state.
 */
function OpsBoardSkeleton() {
  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-3 gap-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex flex-col h-full min-h-0 border border-terminal-border/20 rounded-lg bg-terminal-panel/50">
          <div className="sticky top-0 z-10 px-4 py-3 mb-3 bg-terminal-bg/95 backdrop-blur-sm border-b border-terminal-border/40 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-terminal-muted/50 animate-pulse" />
              <div className="h-4 w-24 bg-terminal-muted/50 rounded animate-pulse" />
              <div className="h-3 w-8 bg-terminal-muted/50 rounded ml-auto animate-pulse" />
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto px-2">
            {[1, 2, 3, 4, 5].map((j) => (
              <div key={j} className="h-16 bg-terminal-bg/50 rounded mb-2 animate-pulse" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function OpsBoard() {
  const { data, loading, error } = useOpsBoard();

  if (error) {
    return (
      <div className="terminal-panel p-4 text-echelon-red border border-echelon-red/30 rounded">
        <div className="font-semibold mb-1">Failed to load ops board</div>
        <div className="text-sm text-terminal-muted">{error}</div>
      </div>
    );
  }

  if (loading && !data) {
    return <OpsBoardSkeleton />;
  }

  // Use optional chaining and default arrays to prevent crashes
  const lanes = data?.lanes ?? {
    new_creations: [],
    about_to_happen: [],
    at_risk: [],
    graduation: [],
  };

  // If no data and not loading, show skeleton (better than blank)
  if (!data) {
    return <OpsBoardSkeleton />;
  }

  // Filter cards for each column based on requirements
  
  // LEFT: New Creations (Sandbox and Pilot timelines)
  const newCreations = (lanes.new_creations ?? []).filter((card) => {
    if (card.type === 'launch') {
      return card.phase === 'sandbox' || card.phase === 'pilot';
    }
    // Include all timeline cards in new_creations lane
    return true;
  });

  // CENTER: Trending (sorted by urgency + signal strength)
  const trending = [...(lanes.about_to_happen ?? [])]
    .sort((a, b) => {
      const d = computeTrendingScore(b) - computeTrendingScore(a);
      if (d !== 0) return d;
      return Date.parse(b.updatedAt) - Date.parse(a.updatedAt);
    });

  // RIGHT: At Risk (plus Breaches panel)
  const atRisk = lanes.at_risk ?? [];

  // Trending status line counts (BullX-like)
  const forksCount = data?.liveNow?.forksLive ?? trending.filter((c) => (c.tags?.includes('fork_soon') || (typeof c.nextForkEtaSec === 'number' && c.nextForkEtaSec <= 900))).length;
  const paradoxCount = data?.liveNow?.paradoxActive ?? trending.filter((c) => c.tags?.includes('paradox_active')).length;
  const disclosuresCount = trending.filter((c) => c.tags?.includes('disclosure_active')).length;
  const flipsCount = trending.filter((c) => c.tags?.includes('evidence_flip')).length;
  const showTrendingStatus = forksCount + paradoxCount + disclosuresCount + flipsCount > 0;

  // Check if we should use tab switcher on mobile (if any list has >10 items)
  const totalCards = newCreations.length + trending.length + atRisk.length;
  const useMobileTabs = totalCards > 10;

  return (
    <div className="flex flex-col h-full">
      {/* Desktop (lg+): Always render the grid */}
      <div className="hidden lg:grid h-full grid-cols-3 gap-3">
        {/* LEFT: Newly Created */}
        <div className="flex flex-col h-full min-h-0 border border-[#00FF41]/20 rounded-lg bg-terminal-panel/50">
          <OpsColumn
            title="Newly Created"
            accentColor="#00FF41"
            cards={newCreations}
            emptyMessage="No new creations"
          />
        </div>

        {/* CENTER: Trending */}
        <div className="flex flex-col h-full min-h-0 border border-[#FF9500]/20 rounded-lg bg-terminal-panel/50">
          <OpsColumn
            title="Trending"
            accentColor="#FF9500"
            cards={trending}
            emptyMessage="No active signals"
            headerBottom={
              showTrendingStatus ? (
                <div className="flex items-center gap-2 pt-1 border-t border-terminal-border/50 text-[10px] text-terminal-muted font-mono">
                  <span className="inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500/80" />
                    Forks: <span className="text-terminal-text font-bold">{forksCount}</span>
                  </span>
                  <span className="opacity-50">·</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500/80" />
                    Paradox: <span className="text-terminal-text font-bold">{paradoxCount}</span>
                  </span>
                  <span className="opacity-50">·</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500/80" />
                    Disclosures: <span className="text-terminal-text font-bold">{disclosuresCount}</span>
                  </span>
                  <span className="opacity-50">·</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500/80" />
                    Flips: <span className="text-terminal-text font-bold">{flipsCount}</span>
                  </span>
                </div>
              ) : null
            }
          />
        </div>

        {/* RIGHT: At Risk + Breaches */}
        <div className="flex flex-col h-full min-h-0 border border-[#FF3B3B]/20 rounded-lg bg-terminal-panel/50">
          <RiskAndResultsColumn atRisk={atRisk} />
        </div>
      </div>

      {/* Mobile: Tabs when crowded, else stacked */}
      <div className="lg:hidden">
        {useMobileTabs ? (
          <MobileTabSwitcher trending={trending} newCreations={newCreations} atRisk={atRisk} />
        ) : (
          <div className="grid grid-cols-1 gap-3">
            <div className="border border-[#00FF41]/20 rounded-lg bg-terminal-panel/50">
              <OpsColumn title="Newly Created" accentColor="#00FF41" cards={newCreations} emptyMessage="No new creations" />
            </div>
            <div className="border border-[#FF9500]/20 rounded-lg bg-terminal-panel/50">
              <OpsColumn title="Trending" accentColor="#FF9500" cards={trending} emptyMessage="No active signals" />
            </div>
            <div className="border border-[#FF3B3B]/20 rounded-lg bg-terminal-panel/50">
              <RiskAndResultsColumn atRisk={atRisk} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Mobile Tab Switcher Component
 * 
 * Shows tabs on mobile when lists are long (>10 items total).
 * Allows switching between the three columns to avoid infinite scrolling.
 */
function MobileTabSwitcher({
  trending,
  newCreations,
  atRisk,
}: {
  trending: OpsCard[];
  newCreations: OpsCard[];
  atRisk: OpsCard[];
}) {
  const [activeTab, setActiveTab] = useState<'active' | 'new' | 'critical'>('active');

  const tabs = [
    { id: 'active' as const, label: 'Trending', count: trending.length, cards: trending, accentColor: '#FF9500', title: 'Trending' },
    { id: 'new' as const, label: 'New', count: newCreations.length, cards: newCreations, accentColor: '#00FF41', title: 'Newly Created' },
    { id: 'critical' as const, label: 'Risk', count: atRisk.length, cards: atRisk, accentColor: '#FF3B3B', title: 'At Risk' },
  ];

  const activeTabData = tabs.find(t => t.id === activeTab)!;

  return (
    <div className="flex-1 min-h-0 flex flex-col mt-1">
      {/* Tab Switcher */}
      <div className="flex items-center gap-2 mb-4 px-4 border-b border-terminal-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition relative ${
              activeTab === tab.id
                ? 'text-terminal-text'
                : 'text-terminal-muted hover:text-terminal-text'
            }`}
          >
            {tab.label}
            <span className="ml-1.5 text-xs text-terminal-muted">({tab.count})</span>
            {activeTab === tab.id && (
              <div
                className="absolute bottom-0 left-0 right-0 h-0.5"
                style={{ backgroundColor: tab.accentColor }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Active Tab Content */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="flex flex-col min-h-0 border border-[#FF9500]/20 rounded-lg bg-terminal-panel/50">
          <OpsColumn
            title={activeTabData.title}
            accentColor={activeTabData.accentColor}
            cards={activeTabData.cards}
            emptyMessage={`No ${activeTabData.label.toLowerCase()} items`}
          />
        </div>
      </div>
    </div>
  );
}
