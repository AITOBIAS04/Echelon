"use client";

import { Handle, Position } from "@xyflow/react";
import { TrendingUp, Globe, Building } from "lucide-react";

interface EventNodeData {
  title: string;
  status: "active" | "resolved-win" | "resolved-loss" | "locked";
  chapter: number;
  eventType: "market" | "geopolitical" | "corporate";
}

interface EventNodeProps {
  data: EventNodeData;
  selected?: boolean;
}

const eventTypeIcons = {
  market: TrendingUp,
  geopolitical: Globe,
  corporate: Building,
};

const statusStyles = {
  active: {
    border: "border-[#f59e0b] border-2",
    animate: "animate-pulse",
    bg: "bg-[#0a0a0f]",
  },
  "resolved-win": {
    border: "border-[#22c55e] border-2",
    animate: "",
    bg: "bg-[#0a0a0f]",
  },
  "resolved-loss": {
    border: "border-[#ef4444] border-2",
    animate: "",
    bg: "bg-[#0a0a0f]",
  },
  locked: {
    border: "border-slate-500 border-2 border-dashed",
    animate: "",
    bg: "bg-[#0a0a0f] opacity-50",
  },
};

export default function EventNode({ data, selected }: EventNodeProps) {
  const Icon = eventTypeIcons[data.eventType];
  const styles = statusStyles[data.status];

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-[#6366f1]" />
      
      <div
        className={`
          w-16 h-16 rounded-full flex items-center justify-center
          ${styles.bg} ${styles.border} ${styles.animate}
          transition-all duration-300 hover:scale-105
          ${selected ? "ring-2 ring-[#6366f1] ring-offset-2 ring-offset-[#0a0a0f]" : ""}
        `}
      >
        <Icon className="w-6 h-6 text-slate-300" />
        
        {/* Chapter badge */}
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-[#6366f1] rounded-full flex items-center justify-center text-xs font-mono text-white">
          {data.chapter}
        </div>
      </div>

      {/* Title below node */}
      <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 w-24">
        <div className="text-xs font-mono text-slate-300 text-center truncate">
          {data.title}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-[#6366f1]" />
    </div>
  );
}


