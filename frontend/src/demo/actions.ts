/**
 * Demo Mode Actions
 * 
 * Provides actions that can be performed in demo mode,
 * such as placing bets and generating activity.
 */

import { demoStore } from "./demoStore";

export const demoActions = {
  placeBet(args: {
    marketId: string | number;
    marketTitle: string;
    outcomeId: "YES" | "NO";
    stake: number;
  }) {
    const snap = demoStore.readOutcome(args.marketId, args.outcomeId);
    const rawPrice = snap?.price ?? 0.5;

    const entryPrice = args.outcomeId === "YES" ? rawPrice : 1 - rawPrice;
    const shares = args.stake / Math.max(0.02, entryPrice);

    const position = {
      id: `p_${Math.random().toString(16).slice(2)}`,
      openedAt: Date.now(),
      marketId: String(args.marketId),
      marketTitle: args.marketTitle,
      outcomeId: args.outcomeId,
      stake: args.stake,
      entryPrice,
      shares,
    };

    demoStore.setPositions([position, ...demoStore.getPositions()]);
    demoStore.pushToast("Position opened", `${args.outcomeId} • £${args.stake.toFixed(2)}`);
  },
};
