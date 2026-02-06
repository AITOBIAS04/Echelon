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
          className="rounded-lg border border-purple-500/20 bg-[#0D0D0D]/90 px-3 py-2 shadow-lg backdrop-blur"
        >
          <div className="text-sm text-slate-100">{t.title}</div>
          {t.detail ? <div className="text-xs text-slate-400">{t.detail}</div> : null}
        </div>
      ))}
    </div>
  );
}
