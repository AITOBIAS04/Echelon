"use client";

import { ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

interface DataRevealProps {
  revealed: boolean;
  children: ReactNode;
  className?: string;
}

export function DataReveal({ revealed, children, className = "" }: DataRevealProps) {
  return (
    <div className={clsx("relative", className)}>
      <motion.div
        animate={{
          filter: revealed ? "blur(0px)" : "blur(12px)",
          opacity: revealed ? 1 : 0.7,
          scale: revealed ? 1 : 0.98,
        }}
        transition={{
          duration: 0.7,
          ease: "easeOut",
        }}
      >
        <AnimatePresence>
          {!revealed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none"
              style={{
                backgroundPosition: "0% 50%",
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                repeatType: "reverse",
                ease: "linear",
              }}
            />
          )}
        </AnimatePresence>
        <div className={clsx(revealed ? "" : "select-none pointer-events-none")}>
          {children}
        </div>
      </motion.div>
    </div>
  );
}
