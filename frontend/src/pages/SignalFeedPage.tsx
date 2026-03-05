/**
 * SignalFeedPage — Route wrapper for the signal feed panel.
 */

import { SignalFeedPanel } from '../components/investigation/SignalFeedPanel';

export function SignalFeedPage() {
  return (
    <div className="max-w-5xl mx-auto p-6">
      <SignalFeedPanel />
    </div>
  );
}
