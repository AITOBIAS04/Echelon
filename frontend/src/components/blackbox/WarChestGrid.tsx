// War Chest Grid Component
// Risk management and exposure tracking

import type { WarChestItem } from '../../types/blackbox';

interface WarChestGridProps {
  items: WarChestItem[];
}

export function WarChestGrid({ items }: WarChestGridProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 16,
        overflow: 'auto',
        padding: 16,
      }}
    >
      {items.map((item) => {
        const riskColor =
          item.riskScore >= 60
            ? 'var(--status-danger)'
            : item.riskScore >= 40
            ? 'var(--status-warning)'
            : 'var(--status-success)';

        return (
          <div
            key={item.id}
            className="panel"
            style={{ cursor: 'pointer' }}
          >
            <div className="panel-header" style={{ padding: '12px 16px' }}>
              <span className="panel-title" style={{ fontSize: 11 }}>{item.id}</span>
              <span
                style={{
                  fontSize: 9,
                  padding: '2px 6px',
                  background: 'var(--status-warning-bg)',
                  color: '#854d0e',
                  borderRadius: 4,
                  fontWeight: 600,
                }}
              >
                ⚠️ ALERT
              </span>
            </div>
            <div style={{ padding: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{item.title}</div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--text-secondary)',
                  marginBottom: 12,
                }}
              >
                <div>
                  Risk Score:{' '}
                  <span style={{ color: riskColor, fontWeight: 600 }}>{item.riskScore}</span>
                </div>
                <div style={{ marginTop: 4 }}>
                  Exposure:{' '}
                  <span style={{ fontFamily: 'var(--font-mono)' }}>
                    ${item.exposure.toLocaleString()}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="action-btn">HEDGE</button>
                <button className="action-btn">CLOSE</button>
                <button
                  className="action-btn"
                  style={{ borderColor: 'var(--status-info)', color: 'var(--status-info)' }}
                >
                  DETAILS
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
