import { useState, useRef, useEffect } from 'react';
import { Bell, X, Plus, ExternalLink } from 'lucide-react';
import { clsx } from 'clsx';
import type { Alert } from '../../types/marketplace';

interface AlertPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// Mock alert data for demo
const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'price',
    icon: '💰',
    title: 'Price Target Hit',
    description: 'ORB_SALVAGE_F7 crossed $4.00',
    theatre: 'ORB_SALVAGE_F7',
    condition: 'Price ≥ $4.00',
    status: 'triggered',
    unread: true,
    time: '14:32:00',
  },
  {
    id: '2',
    type: 'stability',
    icon: '📊',
    title: 'Stability Threshold',
    description: 'Stability dropped below 50%',
    theatre: 'VEN_OIL_TANKER',
    condition: 'Stability < 50%',
    status: 'active',
    unread: true,
    time: '14:28:15',
  },
  {
    id: '3',
    type: 'gap',
    icon: '📐',
    title: 'Logic Gap Alert',
    description: 'Gap exceeded 20% margin',
    theatre: 'FED_RATE_DECISION',
    condition: 'Gap > 20%',
    status: 'active',
    unread: true,
    time: '14:15:30',
  },
  {
    id: '4',
    type: 'volume',
    icon: '📈',
    title: 'Volume Spike',
    description: 'Trading volume increased 3x',
    theatre: 'TAIWAN_STRAIT',
    condition: 'Volume > 200% avg',
    status: 'resolved',
    unread: false,
    time: '13:45:00',
  },
  {
    id: '5',
    type: 'paradox',
    icon: '🔮',
    title: 'Paradox Detected',
    description: 'Contradictory agent signals',
    theatre: 'PUTIN_HEALTH_RUMORS',
    condition: 'Paradox score > 80',
    status: 'active',
    unread: false,
    time: '12:20:00',
  },
];

/**
 * Get alert type styles
 */
function getAlertTypeStyles(type: Alert['type']): { bg: string; border: string; severity: 'critical' | 'warning' | 'info' | 'success' } {
  const styles: Record<string, { bg: string; border: string; severity: 'critical' | 'warning' | 'info' | 'success' }> = {
    price: {
      bg: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.2)',
      severity: 'info',
    },
    stability: {
      bg: 'rgba(250, 204, 21, 0.1)',
      border: 'rgba(250, 204, 21, 0.2)',
      severity: 'warning',
    },
    gap: {
      bg: 'rgba(251, 113, 133, 0.1)',
      border: 'rgba(251, 113, 133, 0.2)',
      severity: 'critical',
    },
    volume: {
      bg: 'rgba(74, 222, 128, 0.1)',
      border: 'rgba(74, 222, 128, 0.2)',
      severity: 'success',
    },
    paradox: {
      bg: 'rgba(139, 92, 246, 0.1)',
      border: 'rgba(139, 92, 246, 0.2)',
      severity: 'warning',
    },
  };

  return styles[type] || styles.price;
}

/**
 * Get status badge styles
 */
function getStatusStyles(status: Alert['status']): { bg: string; text: string; label: string } {
  const styles: Record<string, { bg: string; text: string; label: string }> = {
    triggered: {
      bg: 'rgba(251, 113, 133, 0.2)',
      text: '#FB7185',
      label: 'TRIGGERED',
    },
    active: {
      bg: 'rgba(250, 204, 21, 0.2)',
      text: '#854d0e',
      label: 'ACTIVE',
    },
    resolved: {
      bg: 'rgba(74, 222, 128, 0.2)',
      text: '#4ADE80',
      label: 'RESOLVED',
    },
    paused: {
      bg: 'rgba(100, 116, 139, 0.2)',
      text: '#64748B',
      label: 'PAUSED',
    },
  };

  return styles[status] || styles.active;
}

/**
 * AlertPanel Component
 * 
 * Dropdown panel showing alert notifications:
 * - Price alerts
 * - Stability alerts
 * - Logic gap alerts
 * - Volume alerts
 * - Paradox alerts
 */
export function AlertPanel({ isOpen, onClose }: AlertPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [filter, setFilter] = useState<'all' | 'active' | 'triggered' | 'resolved'>('all');
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'active') return alert.status === 'active';
    if (filter === 'triggered') return alert.status === 'triggered';
    if (filter === 'resolved') return alert.status === 'resolved';
    return true;
  });

  const unreadCount = alerts.filter(a => a.unread).length;

  const markAllRead = () => {
    setAlerts(alerts.map(a => ({ ...a, unread: false })));
  };

  const handleAlertClick = (alertId: string) => {
    setAlerts(alerts.map(a =>
      a.id === alertId ? { ...a, unread: false } : a
    ));
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9998]"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className="fixed top-16 right-4 w-96 max-h-[calc(100vh-8rem)] bg-terminal-panel border border-terminal-border rounded-xl shadow-2xl z-[9999] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border bg-terminal-bg/50">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-status-warning" />
<span className="text-sm font-semibold text-terminal-text">Notifications</span>
            {unreadCount > 0 && (
              <span className="flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-status-danger text-white rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={markAllRead}
              className="text-[10px] text-status-info hover:underline"
            >
              Mark all read
            </button>
            <button
              onClick={onClose}
              className="p-1 text-terminal-muted hover:text-terminal-text transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 px-3 py-2 border-b border-terminal-border bg-terminal-bg/30">
          {(['all', 'active', 'triggered', 'resolved'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                'px-2 py-1 text-[10px] font-medium rounded transition-all',
                filter === f
                  ? 'bg-status-info text-white'
                  : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-bg'
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Alert List */}
        <div className="flex-1 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-terminal-muted">
              <Bell className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">No alerts</p>
            </div>
          ) : (
            filteredAlerts.map(alert => {
              const typeStyles = getAlertTypeStyles(alert.type);
              const statusStyles = getStatusStyles(alert.status);

              return (
                <div
                  key={alert.id}
                  onClick={() => handleAlertClick(alert.id)}
                  className={clsx(
                    'p-3 border-b border-terminal-border last:border-b-0 cursor-pointer transition-colors',
                    alert.unread && 'bg-status-info/5',
                    !alert.unread && 'hover:bg-terminal-card/50'
                  )}
                >
                  <div className="flex gap-3">
                    {/* Icon */}
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                      style={{ backgroundColor: typeStyles.bg }}
                    >
                      {alert.icon}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-sm font-medium text-terminal-text truncate">
                          {alert.title}
                        </span>
                        <span
                          className="text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0"
                          style={{ backgroundColor: statusStyles.bg, color: statusStyles.text }}
                        >
                          {statusStyles.label}
                        </span>
                      </div>

                      <p className="text-xs text-terminal-secondary mb-2">
                        {alert.description}
                      </p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-[10px] text-terminal-muted">
                          <span className="font-mono">{alert.theatre}</span>
                          <span>{alert.time}</span>
                        </div>

                        <span
                          className="text-[10px] font-mono px-2 py-0.5 bg-terminal-bg rounded border border-terminal-border"
                          style={{ color: typeStyles.severity === 'critical' ? '#FB7185' : typeStyles.severity === 'warning' ? '#FACC15' : '#64748B' }}
                        >
                          {alert.condition}
                        </span>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-1.5 mt-2">
                        <button className="flex items-center gap-1 px-2 py-1 text-[10px] bg-terminal-bg border border-terminal-border rounded hover:border-status-info transition-colors">
                          <ExternalLink className="w-3 h-3" />
                          View Theatre
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-terminal-border bg-terminal-bg/50">
          <button className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-status-info/10 border border-status-info/30 rounded-lg text-status-info text-sm font-medium hover:bg-status-info/20 transition-colors">
            <Plus className="w-4 h-4" />
            Create New Alert
          </button>
        </div>
      </div>
    </>
  );
}
