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
        className="fixed inset-0 bg-black/95 backdrop-blur-md z-[9990]"
        onClick={props.onClose}
      />
      <div className="fixed inset-0 z-[9995] flex items-center justify-center">
        <div className="w-[440px] bg-[#0D0D0D] border border-purple-500/40 rounded-lg p-4 shadow-2xl">
          <div className="mb-3">
            <div className="text-xs text-slate-400">Place bet</div>
            <div className="text-base text-slate-100">{props.title}</div>
          </div>

          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm text-slate-300">Side</div>
            <div className="text-sm text-slate-100">{props.side}</div>
          </div>

          <label className="block text-sm text-slate-300">Amount (£)</label>
          <input
            value={stake}
            onChange={(e) => setStake(e.target.value)}
            inputMode="decimal"
            className="mt-1 w-full rounded-md border border-purple-500/20 bg-black/40 px-3 py-2 text-slate-100 outline-none focus:border-purple-500/40"
          />

          <div className="mt-4 flex justify-end gap-2">
            <button
              className="px-3 py-2 rounded-md border border-slate-700/50 text-slate-200 hover:bg-white/5"
              onClick={props.onClose}
            >
              Cancel
            </button>
            <button
              className="px-3 py-2 rounded-md border border-purple-500/40 bg-purple-500/10 text-slate-100 hover:bg-purple-500/15"
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
