import { OpsBoard } from '../components/home/OpsBoard';
import { QuickActionsToolbar } from '../components/home/QuickActionsToolbar';
import { LiveRibbon } from '../components/home/LiveRibbon';

/**
 * HomePage Component
 *
 * High-density 3-column BullX-style grid layout:
 * - LEFT: New Creations (Sandbox and Pilot)
 * - CENTER: Active Alpha (Fork Soon < 10m, Disclosure Active)
 * - RIGHT: Risk & Results (At Risk on top, Recently Graduated on bottom)
 */
export function HomePage() {
  return (
    <div className="h-full min-h-0 flex flex-col overflow-hidden">
      {/* Quick actions + live tape */}
      <div className="flex-shrink-0 px-4 pt-3 pb-2 flex flex-col gap-2">
        <LiveRibbon />
        <QuickActionsToolbar />
      </div>

      {/* Ops board: columns scroll internally */}
      <div className="flex-1 min-h-0 px-4 pb-4 overflow-hidden">
        <OpsBoard />
      </div>
    </div>
  );
}
