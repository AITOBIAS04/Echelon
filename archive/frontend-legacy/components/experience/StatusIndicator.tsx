"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

type Status = "LIVE" | "CRITICAL" | "PROCESSING" | "OFFLINE";

interface StatusIndicatorProps {
  status: Status;
  label?: string;
  className?: string;
}

export function StatusIndicator({
  status,
  label,
  className = "",
}: StatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case "LIVE":
        return {
          bgColor: "bg-[#22c55e]",
          glow: "shadow-[0_0_8px_rgba(34,197,94,0.6)]",
          animate: "animate-pulse",
        };
      case "CRITICAL":
        return {
          bgColor: "bg-[#ef4444]",
          glow: "shadow-[0_0_12px_rgba(239,68,68,0.8)]",
          animate: "animate-pulse",
        };
      case "PROCESSING":
        return {
          bgColor: "bg-[#6366f1]",
          glow: "",
          animate: "animate-spin",
        };
      case "OFFLINE":
        return {
          bgColor: "bg-[#94a3b8]",
          glow: "",
          animate: "",
        };
      default:
        return {
          bgColor: "bg-[#94a3b8]",
          glow: "",
          animate: "",
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={clsx("flex items-center gap-2", className)}>
      {status === "PROCESSING" ? (
        <motion.div
          className={clsx("w-3 h-3", config.bgColor, "rounded-full")}
          animate={{ rotate: 360 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{
            clipPath: "polygon(50% 0%, 0% 100%, 50% 50%)",
          }}
        />
      ) : (
        <motion.div
          className={clsx(
            "w-3 h-3",
            config.bgColor,
            "rounded-full",
            config.glow,
            status === "OFFLINE" && "opacity-50"
          )}
          animate={
            status === "LIVE" || status === "CRITICAL"
              ? {
                  scale: [1, 1.2, 1],
                }
              : {}
          }
          transition={
            status === "LIVE" || status === "CRITICAL"
              ? {
                  repeat: Infinity,
                  duration: 1.5,
                  ease: "easeInOut",
                }
              : {}
          }
        />
      )}
      {label && (
        <span className="text-sm font-mono text-[#94a3b8] uppercase tracking-wider">
          {label}
        </span>
      )}
    </div>
  );
}
