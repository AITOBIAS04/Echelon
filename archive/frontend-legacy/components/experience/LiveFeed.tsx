"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

type FeedLevel = "info" | "success" | "warning" | "danger";

interface FeedItem {
  id: string;
  timestamp: Date | string;
  label: string;
  message: string;
  level: FeedLevel;
}

interface LiveFeedProps {
  items: FeedItem[];
  title?: string;
  className?: string;
}

const levelColors = {
  info: {
    bg: "bg-slate-500/20",
    border: "border-slate-500/30",
    text: "text-slate-300",
    label: "text-slate-400",
  },
  success: {
    bg: "bg-green-500/20",
    border: "border-green-500/30",
    text: "text-green-300",
    label: "text-green-400",
  },
  warning: {
    bg: "bg-amber-500/20",
    border: "border-amber-500/30",
    text: "text-amber-300",
    label: "text-amber-400",
  },
  danger: {
    bg: "bg-red-500/20",
    border: "border-red-500/30",
    text: "text-red-300",
    label: "text-red-400",
  },
};

export function LiveFeed({ items, title = "Live Feed", className = "" }: LiveFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [newItemIds, setNewItemIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Track new items for animation
    const currentIds = new Set(items.map((item) => item.id));
    setNewItemIds(currentIds);

    // Auto-scroll to top when new items arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }

    // Clear animation class after animation completes
    const timer = setTimeout(() => {
      setNewItemIds(new Set());
    }, 500);
    return () => clearTimeout(timer);
  }, [items]);

  const formatTimestamp = (timestamp: Date | string) => {
    const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div
      className={`bg-[#0a0a0f] border border-[#94a3b8]/20 rounded-lg overflow-hidden ${className}`}
      style={{
        backgroundImage: `
          linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: "20px 20px",
      }}
    >
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-[#94a3b8]/20 bg-[#12121a]/50">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-[#ef4444] rounded-full animate-pulse" />
          <span className="text-xs font-mono text-[#94a3b8] uppercase tracking-wider">
            {title}
          </span>
        </div>
      </div>

      {/* Content */}
      <div
        ref={scrollRef}
        className="h-full overflow-y-auto p-4 space-y-2 max-h-[600px]"
        style={{
          scrollbarWidth: "thin",
          scrollbarColor: "#6366f1 #0a0a0f",
        }}
      >
        {items.length === 0 ? (
          <div className="text-center py-8 text-[#94a3b8] font-mono text-sm">
            No feed items
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {items.map((item) => {
              const colors = levelColors[item.level];
              const isNew = newItemIds.has(item.id);

              return (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{
                    duration: 0.3,
                    ease: "easeOut",
                  }}
                  className={clsx(
                    "flex gap-3 items-start p-3 rounded-lg border",
                    colors.bg,
                    colors.border
                  )}
                >
                  <span className="text-xs font-mono text-[#94a3b8]/60 flex-shrink-0 min-w-[80px]">
                    {formatTimestamp(item.timestamp)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className={clsx("text-xs font-mono", colors.label, "mb-0.5")}>
                      {item.label}
                    </div>
                    <div className={clsx("text-sm font-mono", colors.text)}>
                      {item.message}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
