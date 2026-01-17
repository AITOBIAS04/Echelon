import { useMemo } from 'react';
import { useOpsBoard } from '../../hooks/useOpsBoard';
import { LiveNowBar } from './LiveNowBar';
import { TickerCard } from './TickerCard';
import type { OpsCard } from '../../types/opsBoard';

/**
 * Filter cards for TRENDING NOW lane
 * High Quality Score (>80) + High Activity
 */
function filterTrendingNow(cards: OpsCard[]): OpsCard[] {
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
  
  return cards.filter((card) => {
    // High quality score (>80) for launches
    if (card.type === 'launch' && card.qualityScore && card.qualityScore > 80) {
      return true;
    }
    // High stability (>80) + recent activity for timelines
    if (card.type === 'timeline' && card.stability && card.stability > 80) {
      const updatedAt = new Date(card.updatedAt);
      return updatedAt > oneDayAgo;
    }
    return false;
  });
}

/**
 * Filter cards for NEW LAUNCHES lane
 * Created in last 24 hours
 */
function filterNewLaunches(cards: OpsCard[]): OpsCard[] {
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
  
  return cards.filter((card) => {
    const createdAt = new Date(card.createdAt);
    return createdAt > oneDayAgo;
  });
}

/**
 * Filter cards for PARADOX / UNDER THREAT lane
 * paradox_active OR brittle OR sabotage_active
 */
function filterParadoxThreat(cards: OpsCard[]): OpsCard[] {
  return cards.filter((card) => {
    // Check tags
    if (card.tags.includes('paradox_active') || 
        card.tags.includes('brittle') || 
        card.tags.includes('sabotage_heat')) {
      return true;
    }
    // Check paradox proximity
    if (card.paradoxProximity && card.paradoxProximity > 50) {
      return true;
    }
    // Check logic gap (brittle indicator)
    if (card.logicGap && card.logicGap >= 40) {
      return true;
    }
    return false;
  });
}

/**
 * OpsBoard Component
 * 
 * BullX-style 3-strip layout with horizontal scrolling lanes.
 */
export function OpsBoard() {
  const { data, loading, error } = useOpsBoard();

  // Combine all cards from all lanes
  const allCards = useMemo(() => {
    if (!data) return [];
    return [
      ...data.lanes.new_creations,
      ...data.lanes.about_to_happen,
      ...data.lanes.at_risk,
      ...data.lanes.graduation,
    ];
  }, [data]);

  // Filter into 3 categories
  const trendingNow = useMemo(() => filterTrendingNow(allCards), [allCards]);
  const newLaunches = useMemo(() => filterNewLaunches(allCards), [allCards]);
  const paradoxThreat = useMemo(() => filterParadoxThreat(allCards), [allCards]);

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

  return (
    <div className="h-full flex flex-col">
      {/* Live Now Bar */}
      <LiveNowBar liveNow={data.liveNow} />

      {/* Lane A: TRENDING NOW */}
      <div className="mb-2 laptop-compact:mb-4">
        <div className="flex items-center gap-2 mb-2 px-4">
          <span className="text-lg laptop-compact:text-xs">🔥</span>
          <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide laptop-compact:text-xs laptop-compact:font-bold laptop-compact:uppercase laptop-compact:tracking-widest laptop-compact:text-white/50">
            TRENDING NOW
          </h3>
        </div>
        <div
          className="overflow-x-auto scrollbar-hide px-4 laptop-compact:snap-x laptop-compact:snap-mandatory"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            WebkitOverflowScrolling: 'touch',
          }}
        >
          <div className="flex gap-3 pb-2" style={{ minWidth: 'min-content' }}>
            {trendingNow.length === 0 ? (
              <div className="text-terminal-muted text-xs py-4">No trending items</div>
            ) : (
              trendingNow.map((card) => (
                <div key={card.id} className="flex-shrink-0 laptop-compact:snap-start">
                  <TickerCard card={card} />
                </div>
              ))
            )}
          </div>
        </div>
        <style>{`.scrollbar-hide::-webkit-scrollbar { display: none; }`}</style>
      </div>

      {/* Lane B: NEW LAUNCHES */}
      <div className="mb-2 laptop-compact:mb-4">
        <div className="flex items-center gap-2 mb-2 px-4">
          <span className="text-lg laptop-compact:text-xs">🚀</span>
          <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide laptop-compact:text-xs laptop-compact:font-bold laptop-compact:uppercase laptop-compact:tracking-widest laptop-compact:text-white/50">
            NEW LAUNCHES
          </h3>
        </div>
        <div
          className="overflow-x-auto scrollbar-hide px-4 laptop-compact:snap-x laptop-compact:snap-mandatory"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            WebkitOverflowScrolling: 'touch',
          }}
        >
          <div className="flex gap-3 pb-2" style={{ minWidth: 'min-content' }}>
            {newLaunches.length === 0 ? (
              <div className="text-terminal-muted text-xs py-4">No new launches</div>
            ) : (
              newLaunches.map((card) => (
                <div key={card.id} className="flex-shrink-0 laptop-compact:snap-start">
                  <TickerCard card={card} />
                </div>
              ))
            )}
          </div>
        </div>
        <style>{`.scrollbar-hide::-webkit-scrollbar { display: none; }`}</style>
      </div>

      {/* Lane C: PARADOX / UNDER THREAT */}
      <div className="mb-2 laptop-compact:mb-4">
        <div className="flex items-center gap-2 mb-2 px-4">
          <span className="text-lg laptop-compact:text-xs">⚠️</span>
          <h3 className="text-lg font-bold text-terminal-text uppercase tracking-wide laptop-compact:text-xs laptop-compact:font-bold laptop-compact:uppercase laptop-compact:tracking-widest laptop-compact:text-white/50">
            PARADOX / UNDER THREAT
          </h3>
        </div>
        <div
          className="overflow-x-auto scrollbar-hide px-4 laptop-compact:snap-x laptop-compact:snap-mandatory"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            WebkitOverflowScrolling: 'touch',
          }}
        >
          <div className="flex gap-3 pb-2" style={{ minWidth: 'min-content' }}>
            {paradoxThreat.length === 0 ? (
              <div className="text-terminal-muted text-xs py-4">No threats detected</div>
            ) : (
              paradoxThreat.map((card) => (
                <div key={card.id} className="flex-shrink-0 laptop-compact:snap-start">
                  <TickerCard card={card} />
                </div>
              ))
            )}
          </div>
        </div>
        <style>{`.scrollbar-hide::-webkit-scrollbar { display: none; }`}</style>
      </div>
    </div>
  );
}
