"use client";

import { Handle, Position } from "@xyflow/react";
import { Sparkles } from "lucide-react";

interface ProjectedNodeData {
  title: string;
  probability: number; // 0-100
}

interface ProjectedNodeProps {
  data: ProjectedNodeData;
  selected?: boolean;
}

export default function ProjectedNode({ data, selected }: ProjectedNodeProps) {
  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-slate-500" />
      
      <div
        className={`
          w-14 h-14 rounded-full flex flex-col items-center justify-center
          bg-[#0a0a0f] border-2 border-dashed border-slate-500
          opacity-60 transition-all duration-300 hover:scale-105 hover:opacity-80
          animate-pulse
          ${selected ? "ring-2 ring-slate-500 ring-offset-2 ring-offset-[#0a0a0f]" : ""}
        `}
      >
        <Sparkles className="w-4 h-4 text-slate-400 mb-0.5" />
        <span className="text-xs font-mono text-slate-400">
          {data.probability}%
        </span>
      </div>

      {/* Title below node */}
      <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 w-24">
        <div className="text-xs font-mono text-slate-400 text-center truncate">
          {data.title}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-slate-500" />
    </div>
  );
}


