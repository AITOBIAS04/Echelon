/**
 * Demo Bet Modal
 * 
 * Modal for placing demo bets in demo mode.
 * Stylistically aligned with the existing TaskAgentModal pattern.
 */

import React from "react";

export function DemoBetModal(props: {
  open: boolean;
  title: string;
  side: "YES" | "NO";
  onClose: () => void;
  onConfirm: (stake: number) => void;
}) {
  const [stake, setStake] = React.useState("25");

  React.useEffect(() => {
    if (!props.open) return;
    setStake("25");
  }, [props.open]);

  if (!props.open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/95 backdrop-blur-md z-[300]"
        onClick={props.onClose}
      />
      <div className="fixed inset-0 z-[310] flex items-center justify-center">
        <div className="w-[440px] bg-terminal-panel border border-purple-500/40 rounded-lg p-4 shadow-2xl">
          <div className="mb-3">
            <div className="text-xs text-terminal-text-secondary">Place bet</div>
            <div className="text-base text-terminal-text">{props.title}</div>
          </div>

          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm text-terminal-text">Side</div>
            <div className="text-sm text-terminal-text">{props.side}</div>
          </div>

          <label className="block text-sm text-terminal-text">Amount (£)</label>
          <input
            value={stake}
            onChange={(e) => setStake(e.target.value)}
            inputMode="decimal"
            className="mt-1 w-full rounded-md border border-status-paradox/20 bg-black/40 px-3 py-2 text-terminal-text outline-none focus:border-purple-500/40"
          />

          <div className="mt-4 flex justify-end gap-2">
            <button
              className="px-3 py-2 rounded-md border border-terminal-border text-terminal-text hover:bg-white/5"
              onClick={props.onClose}
            >
              Cancel
            </button>
            <button
              className="px-3 py-2 rounded-md border border-purple-500/40 bg-status-paradox/10 text-terminal-text hover:bg-purple-500/15"
              onClick={() => {
                const n = Number(stake);
                if (!Number.isFinite(n) || n <= 0) return;
                props.onConfirm(n);
              }}
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
