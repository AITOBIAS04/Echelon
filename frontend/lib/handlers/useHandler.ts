import { useCallback } from "react";
import { HandlerContext } from "./types";
import { defaultHandler } from "./defaultHandler";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useHandler(handlerId: string = "control", context: HandlerContext = {}) {
  const sendMessage = useCallback(
    async (message: string): Promise<string> => {
      try {
        const response = await fetch(`${API_BASE}/api/handler/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            handler_id: handlerId,
            wallet_address: context.userPositions?.[0]?.id, // Use first position ID as wallet identifier
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response || "No response received.";
      } catch (error) {
        console.error("Error sending message to handler:", error);
        return "Error: Unable to connect to handler service. Please try again.";
      }
    },
    [handlerId, context]
  );

  return {
    handler: defaultHandler, // For now, always use default handler
    sendMessage,
  };
}


