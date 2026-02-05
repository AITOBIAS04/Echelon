import { useState } from 'react';
import { Radio, Filter, TrendingUp, Globe, Ship, Plane } from 'lucide-react';
import { clsx } from 'clsx';

// Mock OSINT signals
const mockSignals = [
  {
    id: 'sig_001',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    source: 'TWITTER',
    category: 'SHIPPING',
    severity: 4,
    confidence: 0.87,
    headline: '3 oil tankers went dark near Strait of Hormuz',
    content: 'AIS signals lost for vessels GLORY STAR, PACIFIC WAVE, and OCEAN FORTUNE...',
    keywords: ['tanker', 'hormuz', 'dark', 'ais'],
    related_timeline: 'TL_GHOST_TANKER',
  },
  {
    id: 'sig_002',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    source: 'NEWS',
    category: 'HEALTH',
    severity: 5,
    confidence: 0.92,
    headline: 'Unusual respiratory illness cluster reported in Mumbai',
    content: 'Health officials investigating 47 cases of unidentified respiratory symptoms...',
    keywords: ['illness', 'mumbai', 'respiratory', 'outbreak'],
    related_timeline: 'TL_CONTAGION',
  },
  {
    id: 'sig_003',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    source: 'FLIGHT_RADAR',
    category: 'POLITICAL',
    severity: 3,
    confidence: 0.75,
    headline: 'Unusual private jet activity from Riyadh to Miami',
    content: '4 Gulfstream jets departed between 2-4 AM local time...',
    keywords: ['jet', 'riyadh', 'miami', 'private'],
    related_timeline: null,
  },
  {
    id: 'sig_004',
    timestamp: new Date(Date.now() - 900000).toISOString(),
    source: 'REDDIT',
    category: 'MARKET',
    severity: 2,
    confidence: 0.65,
    headline: 'WSB unusual activity around energy sector',
    content: 'Spike in mentions of XOM, CVX, OXY in r/wallstreetbets...',
    keywords: ['wsb', 'energy', 'oil', 'stocks'],
    related_timeline: 'TL_OIL_CRISIS',
  },
];

const sourceIcons: Record<string, React.ReactNode> = {
  TWITTER: <Globe className="w-4 h-4" />,
  NEWS: <Radio className="w-4 h-4" />,
  FLIGHT_RADAR: <Plane className="w-4 h-4" />,
  REDDIT: <TrendingUp className="w-4 h-4" />,
  SHIP_TRACKING: <Ship className="w-4 h-4" />,
};

const severityColors: Record<number, string> = {
  1: 'text-terminal-text-muted',
  2: 'text-echelon-blue',
  3: 'text-echelon-amber',
  4: 'text-echelon-red',
  5: 'text-echelon-red animate-pulse',
};

export function OsintFeed() {
  const [filter, setFilter] = useState<string>('ALL');

  const categories = ['ALL', 'SHIPPING', 'HEALTH', 'POLITICAL', 'MARKET'];

  const filteredSignals = filter === 'ALL' ? mockSignals : mockSignals.filter((s) => s.category === filter);

  return (
    <div className="h-full flex flex-col">
      {/* Filter Bar */}
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-terminal-text-muted" />
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={clsx(
              'px-3 py-1 text-xs rounded transition',
              filter === cat
                ? 'bg-echelon-purple/20 text-echelon-purple border border-echelon-purple/30'
                : 'bg-terminal-bg text-terminal-text-muted hover:text-terminal-text'
            )}
          >
            {cat}
          </button>
        ))}
        <div className="ml-auto text-xs text-terminal-text-muted">{filteredSignals.length} signals</div>
      </div>

      {/* Signal Stream */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {filteredSignals.map((signal) => (
          <div key={signal.id} className="terminal-panel p-3">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={severityColors[signal.severity]}>{sourceIcons[signal.source]}</span>
                <span className="text-xs text-terminal-text-muted uppercase">{signal.source}</span>
                <span className="text-xs px-2 py-0.5 bg-terminal-bg rounded text-terminal-text-muted">{signal.category}</span>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className={severityColors[signal.severity]}>SEV-{signal.severity}</span>
                <span className="text-terminal-text-muted">{Math.round(signal.confidence * 100)}% conf</span>
                <span className="text-terminal-text-muted">{formatTimeAgo(new Date(signal.timestamp))}</span>
              </div>
            </div>

            {/* Content */}
            <h3 className="font-medium text-terminal-text mb-1">{signal.headline}</h3>
            <p className="text-sm text-terminal-text-muted mb-2">{signal.content}</p>

            {/* Footer */}
            <div className="flex items-center justify-between">
              <div className="flex gap-1">
                {signal.keywords.map((kw) => (
                  <span key={kw} className="text-xs px-2 py-0.5 bg-terminal-bg rounded text-echelon-cyan">
                    {kw}
                  </span>
                ))}
              </div>
              {signal.related_timeline && <span className="text-xs text-echelon-purple">→ {signal.related_timeline}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

