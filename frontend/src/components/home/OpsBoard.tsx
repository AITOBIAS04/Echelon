import { useState } from 'react';
import { useOpsBoard } from '../../hooks/useOpsBoard';
import { OpsRow } from './OpsRow';
import type { OpsCard, LiveNowSummary } from '../../types/opsBoard';

/**
 * OpsBoard Column Props
 */
interface OpsColumnProps {
  title: string;
  accentColor: string;
  cards: OpsCard[];
  emptyMessage: string;
  liveNow?: LiveNowSummary;
}

/**
 * OpsColumn Component
 * 
 * Individual column in the 3-column grid layout.
 */
function OpsColumn({ title, accentColor, cards, emptyMessage, liveNow }: OpsColumnProps) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Sticky Header */}
      <div
        className="sticky top-0 z-10 flex flex-col gap-2 px-4 py-3 mb-3 bg-terminal-bg/95 backdrop-blur-sm border-b flex-shrink-0"
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
        {/* Live Now Strip - Only in Center column */}
        {liveNow && (
          <div className="flex items-center gap-3 pt-1 border-t border-terminal-border/50">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              <span className="text-[10px] text-terminal-muted font-mono">
                Forks: <span className="text-terminal-text font-bold">{liveNow.forksLive}</span>
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-[#FF3B3B] rounded-full animate-pulse" />
              <span className="text-[10px] text-terminal-muted font-mono">
                Paradox: <span className="text-terminal-text font-bold">{liveNow.paradoxActive}</span>
              </span>
            </div>
          </div>
        )}
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
  recentlyGraduated,
}: {
  atRisk: OpsCard[];
  recentlyGraduated: OpsCard[];
}) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* At Risk Section */}
      <div className="flex flex-col flex-1 min-h-0">
        <div
          className="sticky top-0 z-10 flex items-center gap-2 px-4 py-3 mb-3 bg-terminal-bg/95 backdrop-blur-sm border-b flex-shrink-0"
          style={{ borderColor: '#FF3B3B40' }}
        >
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: '#FF3B3B' }}
          />
          <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">
            🔴 At Risk
          </h3>
          <span className="text-xs text-terminal-muted font-mono ml-auto">
            ({atRisk.length})
          </span>
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
      {atRisk.length > 0 && recentlyGraduated.length > 0 && (
        <div className="h-px bg-terminal-border mx-4 my-2 flex-shrink-0" />
      )}

      {/* Recently Graduated Section */}
      <div className="flex flex-col flex-1 min-h-0">
        <div
          className="sticky top-0 z-10 flex items-center gap-2 px-4 py-3 mb-3 bg-terminal-bg/95 backdrop-blur-sm border-b flex-shrink-0"
          style={{ borderColor: '#AA66FF40' }}
        >
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: '#AA66FF' }}
          />
          <h3 className="text-sm font-bold text-terminal-text uppercase tracking-wide">
            🎓 Recently Graduated
          </h3>
          <span className="text-xs text-terminal-muted font-mono ml-auto">
            ({recentlyGraduated.length})
          </span>
        </div>
        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
          <div className="flex flex-col pb-2">
            {recentlyGraduated.length === 0 ? (
              <div className="text-terminal-muted text-xs py-4 text-center px-4">
                No graduations
              </div>
            ) : (
              recentlyGraduated.map((card) => (
                <OpsRow key={card.id} card={card} />
              ))
            )}
          </div>
        </div>
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
export function OpsBoard() {
  const { data, loading, error } = useOpsBoard();

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-terminal-muted animate-pulse">Loading operations board...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-lg font-semibold text-terminal-text mb-2">Error loading ops board</p>
        <p className="text-sm text-terminal-muted">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Filter cards for each column based on requirements
  
  // LEFT: New Creations (Sandbox and Pilot timelines)
  const newCreations = data.lanes.new_creations.filter((card) => {
    if (card.type === 'launch') {
      return card.phase === 'sandbox' || card.phase === 'pilot';
    }
    // Include all timeline cards in new_creations lane
    return true;
  });

  // CENTER: Active Alpha (Fork Soon ETA < 10m OR Disclosure Active)
  const activeAlpha = data.lanes.about_to_happen.filter((card) => {
    // Fork Soon: nextForkEtaSec < 600 (10 minutes)
    if (card.nextForkEtaSec !== undefined && card.nextForkEtaSec < 600) {
      return true;
    }
    // Disclosure Active tag
    if (card.tags.includes('disclosure_active')) {
      return true;
    }
    // Fork Soon tag
    if (card.tags.includes('fork_soon')) {
      return true;
    }
    return false;
  });

  // RIGHT: Risk & Results (At Risk on top, Recently Graduated on bottom)
  const atRisk = data.lanes.at_risk;
  const recentlyGraduated = data.lanes.graduation;

  // Check if we should use tab switcher on mobile (if any list has >10 items)
  const totalCards = newCreations.length + activeAlpha.length + atRisk.length + recentlyGraduated.length;
  const useMobileTabs = totalCards > 10;

  return (
    <div className="flex flex-col h-full">
      {/* Desktop: 3-Column Grid | Mobile: Stacked or Tabs */}
      {useMobileTabs ? (
        <MobileTabSwitcher
          aboutToHappen={activeAlpha}
          newCreations={newCreations}
          criticalAndGraduating={[...atRisk, ...recentlyGraduated]}
        />
      ) : (
        <div className="h-[calc(100vh-160px)] grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* LEFT: New Creations (Green Accent) */}
          <div className="flex flex-col h-full min-h-0 border border-[#00FF41]/20 rounded-lg bg-terminal-panel/50 order-2 lg:order-1">
            <OpsColumn
              title="🟢 New Creations"
              accentColor="#00FF41"
              cards={newCreations}
              emptyMessage="No new creations"
            />
          </div>

          {/* CENTER: Active Alpha (Orange Accent) - Includes Live Now Strip */}
          <div className="flex flex-col h-full min-h-0 border border-[#FF9500]/20 rounded-lg bg-terminal-panel/50 order-1 lg:order-2">
            <OpsColumn
              title="🟠 Active Alpha"
              accentColor="#FF9500"
              cards={activeAlpha}
              emptyMessage="No active events"
              liveNow={data.liveNow}
            />
          </div>

          {/* RIGHT: Risk & Results (Red/Purple Accent) */}
          <div className="flex flex-col h-full min-h-0 border border-[#FF3B3B]/20 rounded-lg bg-terminal-panel/50 order-3 lg:order-3">
            <RiskAndResultsColumn
              atRisk={atRisk}
              recentlyGraduated={recentlyGraduated}
            />
          </div>
        </div>
      )}
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
  aboutToHappen,
  newCreations,
  criticalAndGraduating,
}: {
  aboutToHappen: OpsCard[];
  newCreations: OpsCard[];
  criticalAndGraduating: OpsCard[];
}) {
  const [activeTab, setActiveTab] = useState<'active' | 'new' | 'critical'>('active');

  const tabs = [
    { id: 'active' as const, label: 'Active', count: aboutToHappen.length, cards: aboutToHappen, accentColor: '#FF9500', title: '🟠 About to Happen' },
    { id: 'new' as const, label: 'New', count: newCreations.length, cards: newCreations, accentColor: '#00FF41', title: '🟢 New Creations' },
    { id: 'critical' as const, label: 'Critical', count: criticalAndGraduating.length, cards: criticalAndGraduating, accentColor: '#FF3B3B', title: '🔴 Critical & Graduating' },
  ];

  const activeTabData = tabs.find(t => t.id === activeTab)!;

  return (
    <div className="flex-1 min-h-0 flex flex-col mt-4 lg:hidden">
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
