/**
 * Handler Component Usage Example
 * 
 * This demonstrates how to integrate the Handler component into your app.
 */

"use client";

import { Handler } from "./Handler";
import { useHandler, HandlerContext } from "@/lib/handlers";

export function HandlerExample() {
  // Create handler context with user's current state
  const context: HandlerContext = {
    currentOperation: {
      id: "op-001",
      codename: "Operation Nightfall",
      description: "High-stakes intelligence operation",
    },
    userPositions: [
      {
        id: "pos-1",
        type: "LONG",
        amount: 1000,
        marketId: "market-1",
      },
    ],
    recentSignals: [
      {
        id: "sig-1",
        type: "ACCUMULATION ALERT",
        message: "CARDINAL accumulating large position",
        timestamp: new Date(),
      },
    ],
    marketState: {
      marketId: "market-1",
      currentPrice: 0.65,
      volume: 50000,
      trend: "bullish",
    },
  };

  // Use the handler hook
  const { handler, sendMessage } = useHandler("control", context);

  return (
    <Handler
      handler={handler}
      context={context}
      onSendMessage={sendMessage}
      defaultExpanded={false}
    />
  );
}

/**
 * Simple integration - just add to your layout or page:
 * 
 * import { Handler } from "@/components/experience";
 * import { useHandler } from "@/lib/handlers";
 * 
 * function YourPage() {
 *   const { handler, sendMessage } = useHandler();
 *   const context = {}; // Your context
 *   
 *   return (
 *     <>
 *       {/* Your page content */}
 *       <Handler 
 *         handler={handler} 
 *         context={context}
 *         onSendMessage={sendMessage}
 *       />
 *     </>
 *   );
 * }
 */


