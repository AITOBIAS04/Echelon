/**
 * Demo Toast Host
 * 
 * Displays toast notifications from the demo store.
 * Mounted once in AppLayout and handles auto-expiration.
 */

import { useDemoToasts } from "./hooks";

export function DemoToastHost() {
  const toasts = useDemoToasts();
  if (toasts.length === 0) return null;

  return (
    <div className="fixed right-4 top-4 z-[500] flex w-[320px] flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="rounded-lg border border-status-paradox/20 bg-terminal-overlay px-3 py-2 shadow-elevation-2 backdrop-blur"
        >
          <div className="text-sm text-terminal-text">{t.title}</div>
          {t.detail ? <div className="text-xs text-terminal-text-secondary">{t.detail}</div> : null}
        </div>
      ))}
    </div>
  );
}
