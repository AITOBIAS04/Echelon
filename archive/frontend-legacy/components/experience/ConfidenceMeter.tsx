"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface ConfidenceMeterProps {
  value: number; // 0-100
  label?: string;
  variant?: "bar" | "compact";
  className?: string;
}

export function ConfidenceMeter({
  value,
  label,
  variant = "bar",
  className = "",
}: ConfidenceMeterProps) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedValue(value);
    }, 100);
    return () => clearTimeout(timer);
  }, [value]);

  const getColor = (val: number) => {
    if (val < 34) return "#ef4444"; // red
    if (val < 67) return "#f59e0b"; // amber
    return "#22c55e"; // green
  };

  const getGradient = () => {
    return `linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%)`;
  };

  if (variant === "compact") {
    return (
      <div className={clsx("flex items-center gap-2", className)}>
        <div className="flex-1 h-1.5 bg-[#12121a] rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            animate={{
              width: `${animatedValue}%`,
            }}
            transition={{
              type: "spring",
              damping: 20,
              stiffness: 100,
            }}
            style={{
              background: getGradient(),
              boxShadow: `0 0 8px ${getColor(animatedValue)}`,
            }}
          />
        </div>
        <span className="text-xs font-mono text-[#94a3b8] min-w-[3rem] text-right">
          {Math.round(animatedValue)}%
        </span>
      </div>
    );
  }

  return (
    <div className={clsx("space-y-2", className)}>
      {label && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-[#94a3b8] font-sans">{label}</span>
          <span className="text-[#e2e8f0] font-mono font-semibold">
            {Math.round(animatedValue)}%
          </span>
        </div>
      )}
      <div className="relative h-3 bg-[#12121a] rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          animate={{
            width: `${animatedValue}%`,
          }}
          transition={{
            type: "spring",
            damping: 20,
            stiffness: 100,
          }}
          style={{
            background: getGradient(),
            boxShadow: `0 0 12px ${getColor(animatedValue)}`,
          }}
        />
      </div>
      {!label && (
        <div className="flex justify-between text-xs font-mono text-[#94a3b8]">
          <span>0%</span>
          <span>100%</span>
        </div>
      )}
    </div>
  );
}
