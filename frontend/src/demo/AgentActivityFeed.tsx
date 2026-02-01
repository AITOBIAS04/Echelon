/**
 * Agent Activity Feed
 * 
 * Displays agent activity events from the demo store.
 * Only renders when demo mode is enabled.
 */

import { useDemoAgentFeed, useDemoEnabled } from "./hooks";

export function AgentActivityFeed() {
  const enabled = useDemoEnabled();
  const feed = useDemoAgentFeed();
  if (!enabled) return null;

  return (
    <div className="bg-[#0D0D0D] border border-purple-500/20 rounded-lg p-3">
      <div className="mb-2 text-sm text-slate-200">Agent activity</div>
      <div className="space-y-2">
        {feed.map((e) => (
          <div key={e.id} className="text-xs text-slate-400">
            <span className="mr-2 text-slate-600">
              {new Date(e.ts).toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
            <span className="text-slate-300">{e.text}</span>
          </div>
        ))}
        {feed.length === 0 ? (
          <div className="text-xs text-slate-500">No recent activity</div>
        ) : null}
      </div>
    </div>
  );
}
