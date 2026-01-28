import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Search, Bell, GitCompare, BarChart3, X, ChevronDown, Cpu, Truck, DollarSign, FlaskConical, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { MarketCard } from '../components/marketplace/MarketCard';
import { LiveRibbon } from '../components/marketplace/LiveRibbon';
import { SignalIntercepts } from '../components/marketplace/SignalIntercepts';
import { ActiveBreaches } from '../components/marketplace/ActiveBreaches';
import { useMarketData, useRibbonEvents, useIntercepts, useBreaches } from '../hooks/useMarketplace';
import { useRegisterTopActionBarActions } from '../contexts/TopActionBarActionsContext';
import type { Alert, CompareSlot } from '../types/marketplace';

// Market categories with icons
const CATEGORIES = [
  { id: 'all', label: 'All Markets', icon: null },
  { id: 'robotics', label: 'Robotics', icon: Cpu },
  { id: 'logistics', label: 'Logistics', icon: Truck },
  { id: 'defi', label: 'DeFi / Econ', icon: DollarSign },
  { id: 'physics', label: 'Physics', icon: FlaskConical },
  { id: 'soceng', label: 'SocEng', icon: Zap },
] as const;

type CategoryId = typeof CATEGORIES[number]['id'];

// Alert type to icon mapping
const ALERT_ICONS: Record<Alert['type'], React.ComponentType<{ className?: string }>> = {
  price: DollarSign,
  stability: BarChart3,
  gap: Zap,
  volume: BarChart3,
  paradox: Zap,
};

// Mock data for alerts
const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'price',
    title: 'Price Target Hit',
    description: 'ORB_SALVAGE_F7 crossed $4.00',
    theatre: 'ORB_SALVAGE_F7',
    condition: 'Price ≥ $4.00',
    status: 'triggered',
    unread: true,
    time: '14:32:00',
    severity: 'critical',
  },
  {
    id: '2',
    type: 'stability',
    title: 'Stability Threshold',
    description: 'Stability dropped below 50%',
    theatre: 'VEN_OIL_TANKER',
    condition: 'Stability < 50%',
    status: 'active',
    unread: true,
    time: '14:28:15',
    severity: 'warning',
  },
  {
    id: '3',
    type: 'gap',
    title: 'Logic Gap Alert',
    description: 'Gap exceeded 20% margin',
    theatre: 'FED_RATE_DECISION',
    condition: 'Gap > 20%',
    status: 'active',
    unread: true,
    time: '14:15:30',
    severity: 'warning',
  },
  {
    id: '4',
    type: 'volume',
    title: 'Volume Spike',
    description: 'Trading volume increased 3x',
    theatre: 'TAIWAN_STRAIT',
    condition: 'Volume > 200% avg',
    status: 'resolved',
    unread: false,
    time: '13:45:00',
    severity: 'success',
  },
  {
    id: '5',
    type: 'paradox',
    title: 'Paradox Detected',
    description: 'Contradictory agent signals',
    theatre: 'PUTIN_HEALTH_RUMORS',
    condition: 'Paradox score > 80',
    status: 'active',
    unread: false,
    time: '12:20:00',
    severity: 'info',
  },
  {
    id: '6',
    type: 'price',
    title: 'Price Target Hit',
    description: 'SPACEX_LAUNCH crossed $3.00',
    theatre: 'SPACEX_LAUNCH',
    condition: 'Price ≥ $3.00',
    status: 'resolved',
    unread: false,
    time: '11:20:00',
    severity: 'success',
  },
];

// Mock data for comparison
const mockCompareTheatres: CompareSlot[] = [
  { id: 'orb_salvage_f7', name: 'ORB_SALVAGE_F7', price: 3.82, change: '+12.4%', stability: 72, gap: 12, volume: '$2.4M', probability: 68, forkIn: '45s' },
  { id: 'ven_oil_tanker', name: 'VEN_OIL_TANKER', price: 2.15, change: '-3.2%', stability: 45, gap: 28, volume: '$890K', probability: 52, forkIn: '2m' },
  { id: 'fed_rate', name: 'FED_RATE_DECISION', price: 3.45, change: '+8.7%', stability: 58, gap: 18, volume: '$1.2M', probability: 61, forkIn: '30s' },
  { id: 'taiwan_strait', name: 'TAIWAN_STRAIT', price: 4.20, change: '-1.5%', stability: 33, gap: 42, volume: '$3.1M', probability: 74, forkIn: '15s' },
  { id: 'putin_health', name: 'PUTIN_HEALTH_RUMORS', price: 1.85, change: '+22.1%', stability: 28, gap: 55, volume: '$567K', probability: 41, forkIn: '5m' },
  { id: 'spacex_launch', name: 'SPACEX_LAUNCH', price: 2.90, change: '+5.3%', stability: 81, gap: 8, volume: '$1.8M', probability: 55, forkIn: '1h' },
];

type SortOption = 'activity' | 'volume' | 'newest' | 'instability';

export function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<CategoryId>('all');
  const [sortBy, setSortBy] = useState<SortOption>('activity');
  
  // Alert system state
  const [alertsPanelOpen, setAlertsPanelOpen] = useState(false);
  const [alertsModalOpen, setAlertsModalOpen] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [alertFilter, setAlertFilter] = useState<'all' | 'active' | 'triggered' | 'resolved'>('all');
  
  // Compare system state
  const [compareSidebarOpen, setCompareSidebarOpen] = useState(false);
  const [compareSlots, setCompareSlots] = useState<(CompareSlot | null)[]>([null, null, null, null]);
  
  const alertPanelRef = useRef<HTMLDivElement>(null);
  const alertBadgeRef = useRef<HTMLButtonElement>(null);

  // Data hooks
  const { data: marketData, isLoading: marketsLoading } = useMarketData();
  const { data: ribbonEvents } = useRibbonEvents();
  const { data: intercepts } = useIntercepts();
  const { data: breaches } = useBreaches();

  // Register TopActionBar button handlers - called at top level since it uses useRef (no re-renders)
  useRegisterTopActionBarActions({
    onAlert: () => setAlertsPanelOpen(true),
    onCompare: () => setCompareSidebarOpen(true),
    onLive: () => {
      // TODO: Implement live toggle functionality if needed
      console.log('Live button clicked - TODO: implement live mode');
    },
    onNewTimeline: () => {
      // TODO: Implement new timeline creation
      console.log('New Timeline button clicked - TODO: implement timeline creation');
    },
  });

  // Filter and sort markets
  const filteredMarkets = useCallback(() => {
    if (!marketData) return [];

    let filtered = [...marketData];

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(m => m.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        m.title.toLowerCase().includes(query) ||
        m.categoryName.toLowerCase().includes(query)
      );
    }

    // Sort
    switch (sortBy) {
      case 'activity':
        filtered.sort((a, b) => b.liquidity - a.liquidity);
        break;
      case 'volume':
        filtered.sort((a, b) => b.volume24h - a.volume24h);
        break;
      case 'newest':
        filtered.sort((a, b) => {
          const idA = typeof a.id === 'number' ? a.id : 0;
          const idB = typeof b.id === 'number' ? b.id : 0;
          return idB - idA;
        });
        break;
      case 'instability':
        filtered.sort((a, b) => b.gap - a.gap);
        break;
    }

    return filtered;
  }, [marketData, selectedCategory, searchQuery, sortBy]);

  // Stats
  const totalMarkets = marketData?.length || 0;
  const totalVolume24h = marketData?.reduce((sum, m) => sum + m.volume24h, 0) || 0;
  const activeForks = marketData?.filter(m => m.nextForkEtaSec && m.nextForkEtaSec < 3600).length || 0;

  // Alert helpers
  const unreadAlertsCount = alerts.filter(a => a.unread).length;

  const handleAlertClick = (alertId: string) => {
    setAlerts(prev => prev.map(a => 
      a.id === alertId ? { ...a, unread: false } : a
    ));
    setAlertsModalOpen(true);
  };
  
  const markAllAlertsRead = () => {
    setAlerts(prev => prev.map(a => ({ ...a, unread: false })));
  };
  
  const toggleAlertStatus = (alertId: string) => {
    setAlerts(prev => prev.map(a => {
      if (a.id === alertId) {
        return {
          ...a,
          status: a.status === 'active' ? 'paused' : 'active'
        };
      }
      return a;
    }));
  };
  
  const deleteAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  };
  
  const openAlertsModal = () => {
    setAlertsPanelOpen(false);
    setAlertsModalOpen(true);
  };
  
  // Compare helpers
  const addToCompareSlot = (slotIndex: number, theatreId: string) => {
    if (!theatreId) return;
    const theatre = mockCompareTheatres.find(t => t.id === theatreId);
    if (theatre) {
      setCompareSlots(prev => {
        const newSlots = [...prev];
        newSlots[slotIndex] = theatre;
        return newSlots;
      });
    }
  };
  
  const removeFromCompareSlot = (slotIndex: number) => {
    setCompareSlots(prev => {
      const newSlots = [...prev];
      newSlots[slotIndex] = null;
      return newSlots;
    });
  };
  
  const clearAllCompareSlots = () => {
    setCompareSlots([null, null, null, null]);
  };
  
  // Close panels when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        alertsPanelOpen &&
        alertPanelRef.current &&
        !alertPanelRef.current.contains(event.target as Node) &&
        alertBadgeRef.current &&
        !alertBadgeRef.current.contains(event.target as Node)
      ) {
        setAlertsPanelOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [alertsPanelOpen]);

  // Filtered alerts for modal
  const filteredAlerts = alerts.filter(alert => {
    if (alertFilter === 'all') return true;
    if (alertFilter === 'active') return alert.status === 'active';
    if (alertFilter === 'triggered') return alert.status === 'triggered';
    if (alertFilter === 'resolved') return alert.status === 'resolved';
    return true;
  });

  // Generate mini bar chart
  const generateMiniBars = () => {
    const bars = [];
    for (let i = 0; i < 10; i++) {
      const height = 20 + Math.random() * 60;
      bars.push(<div key={i} className="mini-bar" style={{ height: `${height}%` }} />);
    }
    return bars;
  };

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#0B0C0E', color: '#F1F5F9', fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Main Content Area */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Controls Bar */}
        <div className="flex-shrink-0 flex items-center gap-4 px-6 py-3" style={{ background: '#0B0C0E', borderBottom: '1px solid #26292E' }}>
          {/* Search */}
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#64748B' }} />
            <input
              type="text"
              placeholder="Search theatres, agents, events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg text-xs"
              style={{ 
                background: '#151719', 
                border: '1px solid #26292E', 
                color: '#F1F5F9',
                outline: 'none'
              }}
            />
          </div>

          {/* Sort Select */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="px-3 py-2 pr-8 rounded-lg text-xs appearance-none cursor-pointer"
              style={{ 
                background: '#151719', 
                border: '1px solid #26292E', 
                color: '#F1F5F9'
              }}
            >
              <option value="activity">Most Active</option>
              <option value="volume">Highest Volume</option>
              <option value="newest">Newest</option>
              <option value="instability">Highest Instability</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#94A3B8' }} />
          </div>

          {/* Stats Bar */}
          <div className="flex items-center gap-6 ml-auto">
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider" style={{ color: '#64748B' }}>Markets</div>
              <div className="font-mono text-xs" style={{ color: '#94A3B8' }}>{totalMarkets}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider" style={{ color: '#64748B' }}>24h Vol</div>
              <div className="font-mono text-xs" style={{ color: '#94A3B8' }}>${(totalVolume24h / 1e6).toFixed(1)}M</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider" style={{ color: '#64748B' }}>Forks</div>
              <div className="font-mono text-xs" style={{ color: '#4ADE80' }}>{activeForks}</div>
            </div>
          </div>
        </div>

        {/* Category Navigation */}
        <div className="flex-shrink-0 flex items-center gap-1 px-6 py-3 overflow-x-auto" style={{ background: '#0B0C0E', borderBottom: '1px solid #26292E' }}>
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all',
                selectedCategory === cat.id
                  ? 'bg-[#151719] border border-[#26292E]'
                  : 'text-[#94A3B8] hover:text-[#F1F5F9]'
              )}
              style={{ 
                background: selectedCategory === cat.id ? '#151719' : 'transparent',
                border: selectedCategory === cat.id ? '1px solid #26292E' : '1px solid transparent',
                color: selectedCategory === cat.id ? '#F1F5F9' : '#94A3B8'
              }}
            >
              {cat.icon && React.createElement(cat.icon, { className: "w-4 h-4" })}
              {cat.label}
            </button>
          ))}
        </div>

        {/* Primary Content Area */}
        <div className="flex-1 min-w-0 flex overflow-hidden">
          {/* Main Content - Left Column */}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
            {/* Live Ribbon */}
            <div className="flex-shrink-0">
              <LiveRibbon events={ribbonEvents || []} />
            </div>

            {/* Market Grid */}
            <div className="flex-1 min-h-0 overflow-y-auto p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#64748B' }}>
                  Active Theatres
                </h2>
                <span className="px-2 py-1 rounded border text-xs font-mono" style={{ 
                  background: '#151719', 
                  borderColor: '#26292E',
                  color: '#94A3B8'
                }}>
                  {filteredMarkets().length}
                </span>
              </div>

              {marketsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="rounded-xl p-4 animate-pulse" style={{ background: '#151719', border: '1px solid #26292E' }}>
                      <div className="h-4 rounded w-1/3 mb-3" style={{ background: '#121417' }} />
                      <div className="h-5 rounded w-3/4 mb-4" style={{ background: '#121417' }} />
                      <div className="flex gap-2 mb-4">
                        <div className="h-12 rounded flex-1" style={{ background: '#121417' }} />
                        <div className="h-12 rounded flex-1" style={{ background: '#121417' }} />
                      </div>
                      <div className="flex gap-2">
                        <div className="h-3 rounded w-1/4" style={{ background: '#121417' }} />
                        <div className="h-3 rounded w-1/4" style={{ background: '#121417' }} />
                        <div className="h-3 rounded w-1/4" style={{ background: '#121417' }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {filteredMarkets().map(market => (
                    <MarketCard key={market.id} market={market} />
                  ))}
                </div>
              )}

              {filteredMarkets().length === 0 && !marketsLoading && (
                <div className="flex flex-col items-center justify-center py-12">
                  <BarChart3 className="w-12 h-12 mb-4" style={{ color: '#64748B', opacity: 0.5 }} />
                  <p className="text-sm" style={{ color: '#64748B' }}>No markets found</p>
                  <p className="text-xs mt-1" style={{ color: '#64748B' }}>Try adjusting your search or filters</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Rail / Aside */}
          <aside className="w-[360px] flex-shrink-0 flex flex-col overflow-y-auto" style={{ background: '#151719', borderLeft: '1px solid #26292E' }}>
            {/* Signal Intercepts - Right Rail */}
            <SignalIntercepts intercepts={intercepts || []} />

            {/* Active Breaches */}
            <ActiveBreaches breaches={breaches || []} />
          </aside>
        </div>
      </div>

      {/* Alert Notification Panel */}
      {alertsPanelOpen && (
        <div 
          ref={alertPanelRef}
          className="fixed top-[60px] right-6 w-[380px] max-h-[calc(100vh-80px)] rounded-xl flex flex-col overflow-hidden z-50 shadow-xl"
          style={{ 
            background: '#151719', 
            border: '1px solid #26292E',
            display: 'flex'
          }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
            <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: '#F1F5F9' }}>
              <Bell className="w-4 h-4" />
              Notifications
              {unreadAlertsCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold" style={{ background: '#FB7185', color: 'white' }}>
                  {unreadAlertsCount}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <button 
                onClick={openAlertsModal}
                className="px-2 py-1 rounded text-[11px] transition-colors"
                style={{ color: '#3B82F6' }}
              >
                Manage All
              </button>
              <button 
                onClick={markAllAlertsRead}
                className="px-2 py-1 rounded text-[11px] transition-colors"
                style={{ color: '#3B82F6' }}
              >
                Mark Read
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {alerts.map(alert => {
              let severityClass = '';
              let severityLabel = '';
              
              if (alert.type === 'gap' || alert.type === 'paradox') {
                if (alert.status === 'triggered') {
                  severityClass = 'critical';
                  severityLabel = 'TRIGGERED';
                } else {
                  severityClass = 'warning';
                  severityLabel = alert.type === 'gap' ? 'GAP' : 'PARADOX';
                }
              } else if (alert.type === 'stability') {
                severityClass = 'warning';
              } else if (alert.type === 'price') {
                severityClass = 'info';
              } else if (alert.type === 'volume') {
                severityClass = 'success';
              }
              
              if (alert.status === 'triggered') {
                severityClass = 'critical';
                severityLabel = 'TRIGGERED';
              } else if (alert.status === 'resolved') {
                severityClass = 'success';
                severityLabel = 'RESOLVED';
              }

              return (
                <div
                  key={alert.id}
                  onClick={() => handleAlertClick(alert.id)}
                  className="flex gap-3 p-3 rounded-lg mb-1 cursor-pointer transition-colors"
                  style={{ 
                    background: alert.unread ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
                    borderLeft: `3px solid ${
                      severityClass === 'critical' ? '#FB7185' :
                      severityClass === 'warning' ? '#FACC15' :
                      severityClass === 'success' ? '#4ADE80' : '#3B82F6'
                    }`
                  }}
                >
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                    style={{ 
                      background: alert.type === 'price' ? 'rgba(59, 130, 246, 0.1)' :
                                 alert.type === 'stability' ? 'rgba(250, 204, 21, 0.1)' :
                                 alert.type === 'gap' ? 'rgba(251, 113, 133, 0.1)' :
                                 alert.type === 'volume' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(139, 92, 246, 0.1)'
                    }}
                  >
                    {React.createElement(ALERT_ICONS[alert.type] || DollarSign, { className: "w-4 h-4" })}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-xs font-semibold" style={{ color: '#F1F5F9' }}>{alert.title}</span>
                      {severityLabel && (
                        <span 
                          className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
                          style={{ 
                            background: severityClass === 'critical' ? 'rgba(251, 113, 133, 0.1)' :
                                       severityClass === 'warning' ? 'rgba(250, 204, 21, 0.1)' :
                                       severityClass === 'success' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(59, 130, 246, 0.1)',
                            color: severityClass === 'critical' ? '#FB7185' :
                                   severityClass === 'warning' ? '#854d0e' :
                                   severityClass === 'success' ? '#4ADE80' : '#3B82F6'
                          }}
                        >
                          {severityLabel}
                        </span>
                      )}
                    </div>
                    <p className="text-xs mb-1" style={{ color: '#94A3B8' }}>{alert.description}</p>
                    <div className="flex gap-2 text-[10px]" style={{ color: '#64748B' }}>
                      <span>{alert.theatre}</span>
                      <span>{alert.time}</span>
                    </div>
                    <div className="flex gap-2 mt-2">
                      <span 
                        className="px-2 py-0.5 rounded text-[10px] font-mono"
                        style={{ background: '#121417', color: '#94A3B8' }}
                      >
                        {alert.condition}
                      </span>
                      <button 
                        className="px-2 py-0.5 rounded text-[10px] transition-colors"
                        style={{ background: 'transparent', border: '1px solid #26292E', color: '#94A3B8' }}
                      >
                        View Theatre
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Alert Management Modal */}
      {alertsModalOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
          onClick={() => setAlertsModalOpen(false)}
        >
          <div 
            className="rounded-xl w-[600px] max-w-[90vw] max-h-[85vh] flex flex-col shadow-xl"
            style={{ background: '#151719', border: '1px solid #26292E' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
              <span className="text-sm font-semibold" style={{ color: '#F1F5F9' }}>Alert Management</span>
              <button 
                onClick={() => setAlertsModalOpen(false)}
                className="p-1 rounded transition-colors"
                style={{ color: '#64748B' }}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              {/* Create Alert Form */}
              <div className="flex flex-col gap-4">
                <div className="flex gap-3">
                  <div className="flex-1 flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold uppercase" style={{ color: '#64748B' }}>Theatre</label>
                    <select 
                      className="px-3 py-2 rounded-lg text-xs appearance-none"
                      style={{ background: '#121417', border: '1px solid #26292E', color: '#F1F5F9' }}
                    >
                      <option value="">Select Theatre...</option>
                      <option value="ORB_SALVAGE_F7">ORB_SALVAGE_F7</option>
                      <option value="VEN_OIL_TANKER">VEN_OIL_TANKER</option>
                      <option value="FED_RATE_DECISION">FED_RATE_DECISION</option>
                      <option value="TAIWAN_STRAIT">TAIWAN_STRAIT</option>
                      <option value="PUTIN_HEALTH_RUMORS">PUTIN_HEALTH_RUMORS</option>
                      <option value="SPACEX_LAUNCH">SPACEX_LAUNCH</option>
                    </select>
                  </div>
                  <div className="flex-1 flex flex-col gap-1.5">
                    <label className="text-[11px] font-semibold uppercase" style={{ color: '#64748B' }}>Alert Type</label>
                    <select 
                      className="px-3 py-2 rounded-lg text-xs appearance-none"
                      style={{ background: '#121417', border: '1px solid #26292E', color: '#F1F5F9' }}
                    >
                      <option value="price">Price Target</option>
                      <option value="stability">Stability</option>
                      <option value="gap">Logic Gap</option>
                      <option value="volume">Volume</option>
                      <option value="paradox">Paradox</option>
                    </select>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-semibold uppercase" style={{ color: '#64748B' }}>Condition</label>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: '#121417', border: '1px solid #26292E' }}>
                    <select 
                      className="bg-transparent border-none text-xs outline-none"
                      style={{ color: '#F1F5F9' }}
                    >
                      <option value="Price">Price</option>
                      <option value="Probability">Probability</option>
                      <option value="Stability">Stability</option>
                      <option value="Volume">Volume</option>
                    </select>
                    <span className="font-mono text-xs font-semibold" style={{ color: '#3B82F6' }}>≥</span>
                    <input 
                      type="text" 
                      placeholder="Value (e.g., 4.00 or 50%)"
                      className="flex-1 bg-transparent border-none text-xs outline-none font-mono"
                      style={{ color: '#F1F5F9' }}
                    />
                  </div>
                </div>
                <button 
                  className="px-4 py-2 rounded-lg text-xs font-semibold self-start transition-colors"
                  style={{ background: '#3B82F6', color: 'white' }}
                >
                  Create Alert
                </button>
              </div>

              <hr className="my-5" style={{ border: 'none', borderTop: '1px solid #26292E' }} />

              {/* Filter Tabs */}
              <div className="flex gap-2 mb-4">
                {(['all', 'active', 'triggered', 'resolved'] as const).map(filter => (
                  <button
                    key={filter}
                    onClick={() => setAlertFilter(filter)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                    style={{ 
                      background: alertFilter === filter ? '#3B82F6' : 'transparent',
                      border: `1px solid ${alertFilter === filter ? '#3B82F6' : '#26292E'}`,
                      color: alertFilter === filter ? 'white' : '#94A3B8'
                    }}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>

              {/* Alerts List */}
<div className="flex flex-col gap-2">
                {filteredAlerts.map(alert => (
                  <div 
                    key={alert.id}
                    className="flex gap-3 p-3 rounded-lg"
                    style={{ 
                      background: '#121417', 
                      border: '1px solid #26292E',
                      borderColor: alert.unread ? '#3B82F6' : '#26292E'
                    }}
                  >
                    <div 
                      className="w-9 h-9 rounded-full flex items-center justify-center text-base flex-shrink-0"
                      style={{ 
                        background: alert.type === 'price' ? 'rgba(59, 130, 246, 0.1)' :
                                   alert.type === 'stability' ? 'rgba(250, 204, 21, 0.1)' :
                                   alert.type === 'gap' ? 'rgba(251, 113, 133, 0.1)' :
                                   alert.type === 'volume' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(139, 92, 246, 0.1)'
                      }}
                    >
                      {React.createElement(ALERT_ICONS[alert.type] || DollarSign, { className: "w-4 h-4" })}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs font-semibold" style={{ color: '#F1F5F9' }}>{alert.title}</span>
                        <span className="text-[10px]" style={{ color: '#64748B' }}>{alert.time}</span>
                      </div>
                      <p className="text-xs mb-1" style={{ color: '#94A3B8' }}>{alert.description}</p>
                      <span 
                        className="inline-block px-2 py-0.5 rounded text-[10px] font-mono mb-2"
                        style={{ background: '#151719', color: '#94A3B8' }}
                      >
                        {alert.condition}
                      </span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <button 
                        onClick={() => toggleAlertStatus(alert.id)}
                        className="px-2 py-1 rounded text-[10px] transition-colors"
                        style={{ background: 'transparent', border: '1px solid #26292E', color: '#94A3B8' }}
                      >
                        {alert.status === 'active' ? 'Pause' : 'Enable'}
                      </button>
                      <button 
                        onClick={() => deleteAlert(alert.id)}
                        className="px-2 py-1 rounded text-[10px] transition-colors"
                        style={{ background: 'transparent', border: '1px solid #26292E', color: '#FB7185' }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-3 px-5 py-4 border-t" style={{ background: '#121417', borderColor: '#26292E' }}>
              <button 
                onClick={() => setAlertsModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium transition-colors"
                style={{ background: '#121417', border: '1px solid #26292E', color: '#94A3B8' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Compare Sidebar */}
      <div 
        className={`fixed top-0 h-full shadow-xl z-[1500] flex flex-col transition-all duration-300 ease-out ${compareSidebarOpen ? 'right-0' : 'right-[-480px]'}`}
        style={{ 
          width: '480px',
          background: '#151719', 
          borderLeft: '1px solid #26292E'
        }}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ background: '#121417', borderColor: '#26292E' }}>
          <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: '#F1F5F9' }}>
            <GitCompare className="w-4 h-4" />
            Compare Theatres
          </div>
          <button 
            onClick={() => setCompareSidebarOpen(false)}
            className="p-1 rounded transition-colors"
            style={{ color: '#64748B' }}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Compare Grid */}
        <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-px" style={{ background: '#26292E' }}>
          {compareSlots.map((slot, index) => (
            <div 
              key={index}
              className={`p-4 flex flex-col gap-3 overflow-y-auto ${!slot ? 'items-center justify-center' : ''}`}
              style={{ background: '#151719' }}
            >
              {slot ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold" style={{ color: '#F1F5F9' }}>{slot.name}</span>
                    <button 
                      onClick={() => removeFromCompareSlot(index)}
                      className="text-lg leading-none opacity-0 hover:opacity-100 transition-opacity"
                      style={{ color: '#64748B' }}
                    >
                      ×
                    </button>
                  </div>
                  {/* Mini Chart */}
                  <div className="h-[60px] rounded flex items-end gap-0.5 p-1" style={{ background: '#121417' }}>
                    {generateMiniBars()}
                  </div>
                  {/* Metrics */}
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Price</span>
                      <span className="font-mono text-xs font-semibold" style={{ color: '#94A3B8' }}>${slot.price.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>24h</span>
                      <span className={`font-mono text-xs font-semibold ${slot.change.includes('+') ? 'text-[#4ADE80]' : 'text-[#FB7185]'}`}>
                        {slot.change}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Stability</span>
                      <span 
                        className="font-mono text-xs font-semibold"
                        style={{ 
                          color: slot.stability > 60 ? '#4ADE80' : slot.stability > 40 ? '#FACC15' : '#FB7185'
                        }}
                      >
                        {slot.stability}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Gap</span>
                      <span 
                        className="font-mono text-xs font-semibold"
                        style={{ 
                          color: slot.gap > 40 ? '#FB7185' : slot.gap > 25 ? '#FACC15' : '#4ADE80'
                        }}
                      >
                        {slot.gap}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Prob.</span>
                      <span className="font-mono text-xs font-semibold" style={{ color: '#94A3B8' }}>{slot.probability}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Volume</span>
                      <span className="font-mono text-xs font-semibold" style={{ color: '#94A3B8' }}>{slot.volume}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px]" style={{ color: '#64748B' }}>Fork In</span>
                      <span className="font-mono text-xs font-semibold" style={{ color: '#94A3B8' }}>{slot.forkIn}</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center w-full">
                  <span className="text-2xl block mb-3" style={{ color: '#64748B' }}>+</span>
                  <select 
                    onChange={(e) => addToCompareSlot(index, e.target.value)}
                    className="w-full px-2 py-1.5 rounded text-xs appearance-none cursor-pointer mb-2"
                    style={{ background: '#121417', border: '1px solid #26292E', color: '#F1F5F9' }}
                  >
                    <option value="">Select Theatre...</option>
                    {mockCompareTheatres.map(theatre => (
                      <option key={theatre.id} value={theatre.id}>{theatre.name}</option>
                    ))}
                  </select>
                  <span className="text-[11px]" style={{ color: '#64748B' }}>Click to add</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Comparison Charts */}
        {compareSlots.filter(s => s).length >= 2 && (() => {
          const selectedTheatres = compareSlots.filter((s): s is CompareSlot => s !== null);
          const maxStability = Math.max(...selectedTheatres.map(t => t.stability));
          const maxGap = Math.max(...selectedTheatres.map(t => t.gap));
          
          return (
            <div className="p-4 border-t" style={{ background: '#121417', borderColor: '#26292E' }}>
              <div className="mb-4">
                <span className="text-[10px] font-semibold uppercase mb-2 block" style={{ color: '#64748B' }}>Stability Comparison</span>
                {selectedTheatres.map(theatre => (
                  <div key={theatre.id} className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-[10px]" style={{ color: '#94A3B8', width: '90px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {theatre.name.replace('_', ' ')}
                    </span>
                    <div className="flex-1 h-4 rounded" style={{ background: '#151719' }}>
                      <div 
                        className="h-full rounded"
                        style={{ 
                          width: `${(theatre.stability / maxStability) * 100}%`,
                          background: theatre.stability > 60 ? '#4ADE80' : theatre.stability > 40 ? '#FACC15' : '#FB7185'
                        }}
                      />
                    </div>
                    <span className="font-mono text-xs font-semibold" style={{ color: '#F1F5F9', width: '40px', textAlign: 'right' }}>{theatre.stability}%</span>
                  </div>
                ))}
              </div>
              <div>
                <span className="text-[10px] font-semibold uppercase mb-2 block" style={{ color: '#64748B' }}>Gap Comparison</span>
                {selectedTheatres.map(theatre => (
                  <div key={theatre.id} className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-[10px]" style={{ color: '#94A3B8', width: '90px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {theatre.name.replace('_', ' ')}
                    </span>
                    <div className="flex-1 h-4 rounded" style={{ background: '#151719' }}>
                      <div 
                        className="h-full rounded"
                        style={{ 
                          width: `${(theatre.gap / maxGap) * 100}%`,
                          background: theatre.gap > 40 ? '#FB7185' : theatre.gap > 25 ? '#FACC15' : '#4ADE80'
                        }}
                      />
                    </div>
                    <span className="font-mono text-xs font-semibold" style={{ color: '#F1F5F9', width: '40px', textAlign: 'right' }}>{theatre.gap}%</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}

        {/* Footer Actions */}
        <div className="px-5 py-4 border-t" style={{ background: '#121417', borderColor: '#26292E' }}>
          <div className="flex gap-2">
            <button 
              onClick={clearAllCompareSlots}
              className="flex-1 px-4 py-2 rounded-lg text-xs font-semibold transition-colors"
              style={{ background: '#151719', border: '1px solid #26292E', color: '#94A3B8' }}
            >
              Clear All
            </button>
            <button 
              className="flex-1 px-4 py-2 rounded-lg text-xs font-semibold transition-colors"
              style={{ background: '#151719', border: '1px solid #26292E', color: '#94A3B8' }}
            >
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Global styles for mini bar charts */}
      <style>{`
        .mini-bar {
          flex: 1;
          background: #3B82F6;
          border-radius: 2px 2px 0 0;
          opacity: 0.7;
        }
      `}</style>
    </div>
  );
}
