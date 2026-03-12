import { Suspense } from 'react';
import '../../styles/public.css';

/**
 * PublicShell — Wraps public-facing pages in the `.public-shell` scope
 * so public.css design tokens apply correctly when rendered inside AppLayout.
 *
 * Use this instead of PublicLayout when embedding public pages within the
 * operator shell (sidebar + header visible).
 */
export function PublicShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="public-shell">
      <Suspense
        fallback={
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Loading...
          </div>
        }
      >
        {children}
      </Suspense>
    </div>
  );
}
