import { useState } from 'react';
import { useOpsBoard } from '../../hooks/useOpsBoard';
import { LiveNowBar } from './LiveNowBar';
import { TickerCard } from './TickerCard';
import type { OpsCard } from '../../types/opsBoard';

/**
 * OpsBoard Column Props
 */
interface OpsColumnProps {
  title: string;
  accentColor: string;
  cards: OpsCard[];
  emptyMessage: string;
}

/**
 * OpsColumn Component
 * 
 * Individual column in the 3-column grid layout.
 */
function OpsColumn({ title, accentColor, cards, emptyMessage }: OpsColumnProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Sticky Header */}
      <div
        className="sticky top-0 z-10 flex items-center gap-2 px-4 py-3 mb-3 bg-terminal-bg/95 backdrop-blur-sm border-b"
        style={{ borderColor: `${accentColor}40` }}
      >
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

      {/* Cards List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        <div className="flex flex-col gap-3 px-4 pb-4">
          {cards.length === 0 ? (
            <div className="text-terminal-muted text-xs py-8 text-center">
              {emptyMessage}
            </div>
          ) : (
            cards.map((card) => (
              <TickerCard key={card.id} card={card} />
            ))
          )}
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

  // Combine at_risk and graduation into Column 3
  const criticalAndGraduating = [
    ...data.lanes.at_risk,
    ...data.lanes.graduation,
  ];

  // Check if we should use tab switcher on mobile (if any list has >10 items)
  const totalCards = data.lanes.about_to_happen.length + data.lanes.new_creations.length + criticalAndGraduating.length;
  const useMobileTabs = totalCards > 10;

  return (
    <div className="flex flex-col h-full">
      {/* Live Now Bar */}
      <LiveNowBar liveNow={data.liveNow} />

      {/* Desktop: 3-Column Grid | Mobile: Stacked or Tabs */}
      {useMobileTabs ? (
        <MobileTabSwitcher
          aboutToHappen={data.lanes.about_to_happen}
          newCreations={data.lanes.new_creations}
          criticalAndGraduating={criticalAndGraduating}
        />
      ) : (
        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
          {/* Mobile Order: About to Happen first (most urgent) */}
          {/* Column 2: About to Happen (Orange Accent) */}
          <div className="flex flex-col min-h-0 border border-[#FF9500]/20 rounded-lg bg-terminal-panel/50 order-1 lg:order-2">
            <OpsColumn
              title="🟠 About to Happen"
              accentColor="#FF9500"
              cards={data.lanes.about_to_happen}
              emptyMessage="No upcoming events"
            />
          </div>

          {/* Column 1: New Creations (Green Accent) */}
          <div className="flex flex-col min-h-0 border border-[#00FF41]/20 rounded-lg bg-terminal-panel/50 order-2 lg:order-1">
            <OpsColumn
              title="🟢 New Creations"
              accentColor="#00FF41"
              cards={data.lanes.new_creations}
              emptyMessage="No new creations"
            />
          </div>

          {/* Column 3: Critical & Graduating (Red/Purple Accent) */}
          <div className="flex flex-col min-h-0 border border-[#FF3B3B]/20 rounded-lg bg-terminal-panel/50 order-3 lg:order-3">
            <OpsColumn
              title="🔴 Critical & Graduating"
              accentColor="#FF3B3B"
              cards={criticalAndGraduating}
              emptyMessage="No critical items"
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
