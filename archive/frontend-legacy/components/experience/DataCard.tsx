"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

type Priority = "none" | "success" | "warning" | "danger";

interface DataCardProps {
  title?: string;
  subtitle?: string;
  priority?: Priority;
  headerAddon?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function DataCard({
  title,
  subtitle,
  priority = "none",
  headerAddon,
  children,
  footer,
  className = "",
  onClick,
}: DataCardProps) {
  const getPriorityBorder = () => {
    switch (priority) {
      case "success":
        return "border-l-[#22c55e]";
      case "warning":
        return "border-l-[#f59e0b]";
      case "danger":
        return "border-l-[#ef4444]";
      default:
        return "";
    }
  };

  const borderWidth = priority !== "none" ? "border-l-2" : "";

  const getHoverShadow = () => {
    if (!onClick) return undefined;
    switch (priority) {
      case "success":
        return "0 0 20px rgba(34,197,94,0.2)";
      case "warning":
        return "0 0 20px rgba(245,158,11,0.2)";
      case "danger":
        return "0 0 20px rgba(239,68,68,0.2)";
      default:
        return "0 0 20px rgba(99,102,241,0.1)";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      whileHover={
        onClick
          ? {
              scale: 1.02,
              y: -2,
              boxShadow: getHoverShadow(),
            }
          : undefined
      }
      className={clsx(
        "relative",
        "bg-[#12121a]/80",
        "backdrop-blur-md",
        "border border-[#94a3b8]/20",
        "rounded-lg",
        borderWidth,
        getPriorityBorder(),
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      {/* Header */}
      {(title || subtitle || headerAddon) && (
        <div className="px-4 py-3 border-b border-[#94a3b8]/10">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-base font-semibold text-[#e2e8f0] font-sans mb-0.5">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-[#94a3b8] font-sans">{subtitle}</p>
              )}
            </div>
            {headerAddon && <div className="flex-shrink-0">{headerAddon}</div>}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="px-4 py-4">{children}</div>

      {/* Footer */}
      {footer && (
        <div className="px-4 py-3 border-t border-[#94a3b8]/10">{footer}</div>
      )}
    </motion.div>
  );
}
