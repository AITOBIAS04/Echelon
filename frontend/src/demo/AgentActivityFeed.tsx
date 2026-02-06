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
    <div className="bg-terminal-panel border border-status-paradox/20 rounded-lg p-3">
      <div className="mb-2 text-sm text-terminal-text">Agent activity</div>
      <div className="space-y-2">
        {feed.map((e) => (
          <div key={e.id} className="text-xs text-terminal-text-secondary">
            <span className="mr-2 text-terminal-text-muted">
              {new Date(e.ts).toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
            <span className="text-terminal-text">{e.text}</span>
          </div>
        ))}
        {feed.length === 0 ? (
          <div className="text-xs text-terminal-text-muted">No recent activity</div>
        ) : null}
      </div>
    </div>
  );
}
