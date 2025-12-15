"use client";

import { Handle, Position } from "@xyflow/react";
import { ProgressRing } from "../";

interface MilestoneNodeData {
  title: string;
  chapter: number;
  progress?: number; // 0-100
}

interface MilestoneNodeProps {
  data: MilestoneNodeData;
  selected?: boolean;
}

export default function MilestoneNode({ data, selected }: MilestoneNodeProps) {
  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-[#f59e0b]" />
      
      <div className="flex flex-col items-center">
        {/* Hexagon shape */}
        <div
          className={`
            w-20 h-20 flex items-center justify-center
            transition-all duration-300 hover:scale-105
            ${selected ? "ring-2 ring-[#f59e0b] ring-offset-2 ring-offset-[#0a0a0f]" : ""}
          `}
          style={{
            clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
            background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
          }}
        >
          {data.progress !== undefined ? (
            <ProgressRing
              value={data.progress}
              size={60}
              showLabel={false}
              color="#0a0a0f"
            />
          ) : (
            <span className="text-2xl font-mono font-bold text-[#0a0a0f]">
              {data.chapter}
            </span>
          )}
        </div>

        {/* Title below hexagon */}
        <div className="mt-2 w-32">
          <div className="text-xs font-mono text-[#f59e0b] text-center truncate">
            {data.title}
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-[#f59e0b]" />
    </div>
  );
}

