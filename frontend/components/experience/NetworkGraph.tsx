"use client";

import React, { useCallback, useMemo } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import EventNode from "./nodes/EventNode";
import MilestoneNode from "./nodes/MilestoneNode";
import ProjectedNode from "./nodes/ProjectedNode";

const nodeTypes = {
  event: EventNode,
  milestone: MilestoneNode,
  projected: ProjectedNode,
};

interface NetworkGraphProps {
  storylineId: string;
  onNodeClick: (nodeId: string, nodeData: any) => void;
  initialNodes?: Node[];
  initialEdges?: Edge[];
}

// Mock data for "The Tanker War" storyline
const defaultNodes: Node[] = [
  {
    id: "ch1",
    type: "event",
    position: { x: 50, y: 150 },
    data: {
      title: "Ghost Ships",
      status: "resolved-win",
      chapter: 1,
      eventType: "geopolitical",
    },
  },
  {
    id: "ch2",
    type: "event",
    position: { x: 250, y: 150 },
    data: {
      title: "Strait Tensions",
      status: "active",
      chapter: 2,
      eventType: "geopolitical",
    },
  },
  {
    id: "ch3a",
    type: "projected",
    position: { x: 450, y: 80 },
    data: {
      title: "Naval Blockade",
      probability: 65,
    },
  },
  {
    id: "ch3b",
    type: "projected",
    position: { x: 450, y: 220 },
    data: {
      title: "De-escalation",
      probability: 35,
    },
  },
  {
    id: "ch4",
    type: "milestone",
    position: { x: 650, y: 150 },
    data: {
      title: "Resolution",
      chapter: 4,
      progress: 0,
    },
  },
];

const defaultEdges: Edge[] = [
  {
    id: "e1-2",
    source: "ch1",
    target: "ch2",
    animated: true,
    style: { stroke: "#f59e0b", strokeWidth: 2 },
    markerEnd: {
      type: "arrowclosed",
      color: "#f59e0b",
    },
  },
  {
    id: "e2-3a",
    source: "ch2",
    target: "ch3a",
    style: { stroke: "#64748b", strokeWidth: 1 },
    markerEnd: {
      type: "arrowclosed",
      color: "#64748b",
    },
  },
  {
    id: "e2-3b",
    source: "ch2",
    target: "ch3b",
    style: { stroke: "#64748b", strokeWidth: 1 },
    markerEnd: {
      type: "arrowclosed",
      color: "#64748b",
    },
  },
  {
    id: "e3a-4",
    source: "ch3a",
    target: "ch4",
    style: { stroke: "#64748b", strokeWidth: 1, strokeDasharray: "5,5" },
    markerEnd: {
      type: "arrowclosed",
      color: "#64748b",
    },
  },
  {
    id: "e3b-4",
    source: "ch3b",
    target: "ch4",
    style: { stroke: "#64748b", strokeWidth: 1, strokeDasharray: "5,5" },
    markerEnd: {
      type: "arrowclosed",
      color: "#64748b",
    },
  },
];

export default function NetworkGraph({
  storylineId,
  onNodeClick,
  initialNodes,
  initialEdges,
}: NetworkGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialNodes || defaultNodes
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges || defaultEdges
  );

  const onNodeClickHandler = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeClick(node.id, node.data);
    },
    [onNodeClick]
  );

  // Custom styles for dark theme
  const flowStyles = useMemo(
    () => ({
      background: "#0a0a0f",
      width: "100%",
      height: "100%",
    }),
    []
  );

  return (
    <div className="w-full h-full bg-[#0a0a0f]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        fitView
        style={flowStyles}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#1e293b"
          className="opacity-30"
        />
        <Controls
          className="!bg-[#12121a] !border-slate-700"
          style={{
            button: {
              backgroundColor: "#12121a",
              color: "#94a3b8",
              borderColor: "#475569",
            },
          }}
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.type === "event") {
              const status = node.data?.status;
              if (status === "active") return "#f59e0b";
              if (status === "resolved-win") return "#22c55e";
              if (status === "resolved-loss") return "#ef4444";
              return "#64748b";
            }
            if (node.type === "milestone") return "#f59e0b";
            if (node.type === "projected") return "#64748b";
            return "#6366f1";
          }}
          maskColor="rgba(10, 10, 15, 0.8)"
          className="!bg-[#12121a] !border-slate-700"
          style={{
            backgroundColor: "#12121a",
          }}
        />
      </ReactFlow>

      {/* Custom CSS overrides for dark theme */}
      <style jsx global>{`
        .react-flow__node {
          cursor: pointer;
        }

        .react-flow__node.selected {
          outline: none;
        }

        .react-flow__edge-path {
          stroke-width: 2;
        }

        .react-flow__edge.animated .react-flow__edge-path {
          stroke-dasharray: 5;
          animation: dashdraw 0.5s linear infinite;
        }

        @keyframes dashdraw {
          to {
            stroke-dashoffset: -10;
          }
        }

        .react-flow__controls {
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        .react-flow__controls-button {
          background-color: #12121a;
          border-color: #475569;
          color: #94a3b8;
        }

        .react-flow__controls-button:hover {
          background-color: #1e293b;
          color: #e2e8f0;
        }

        .react-flow__minimap {
          background-color: #12121a;
          border: 1px solid #475569;
        }

        .react-flow__minimap-mask {
          fill: rgba(10, 10, 15, 0.8);
        }

        .react-flow__minimap-node {
          fill: #475569;
        }
      `}</style>
    </div>
  );
}



