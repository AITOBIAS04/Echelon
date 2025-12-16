/**
 * OperationCentre Usage Example
 * 
 * This demonstrates how to use the OperationCentre component
 * to replace the old mission system.
 */

"use client";

import { OperationCentre } from "./OperationCentre";

// Example usage in a page component
export function OperationCentreExample() {
  const mockIntelSources = [
    {
      id: "cardinal",
      name: "CARDINAL",
      accuracy: 87,
      cost: 25,
      accessed: false,
      data: {
        keyFacts: [
          "High-level source indicates 73% probability of success",
          "Three independent confirmations received",
          "Timeline: 18-24 hours",
        ],
        metrics: [
          { label: "Confidence", value: "87%" },
          { label: "Source Reliability", value: "A+" },
          { label: "Last Update", value: "2h ago" },
        ],
        confidence: 87,
        timestamp: new Date().toISOString(),
      },
    },
    {
      id: "sentinel",
      name: "SENTINEL",
      accuracy: 72,
      cost: 15,
      accessed: false,
      data: {
        keyFacts: [
          "Market signals show bullish trend",
          "Volume spike detected 4h ago",
        ],
        metrics: [
          { label: "Confidence", value: "72%" },
          { label: "Source Reliability", value: "B+" },
        ],
        confidence: 72,
        timestamp: new Date().toISOString(),
      },
    },
    {
      id: "raven",
      name: "RAVEN",
      accuracy: 65,
      cost: 10,
      accessed: false,
    },
  ];

  const handleIntelAccess = async (sourceId: string) => {
    // Call your API to purchase intel
    console.log(`Accessing intel source: ${sourceId}`);
    // await fetch(`/api/intel/${sourceId}/purchase`, { method: "POST" });
  };

  const handlePositionBuild = async (position: any) => {
    // Call your API to build position
    console.log("Building position:", position);
    // await fetch(`/api/positions`, { 
    //   method: "POST", 
    //   body: JSON.stringify(position) 
    // });
  };

  return (
    <OperationCentre
      operationId="op-001"
      operationTitle="Operation Nightfall"
      operationDescription="High-stakes intelligence operation with multiple intel sources available"
      intelSources={mockIntelSources}
      onIntelAccess={handleIntelAccess}
      onPositionBuild={handlePositionBuild}
      onOperationComplete={() => console.log("Operation complete")}
    />
  );
}


