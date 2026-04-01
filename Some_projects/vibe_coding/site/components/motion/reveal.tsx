"use client";

import * as React from "react";
import { motion, type MotionProps, useInView } from "framer-motion";

import { cn } from "@/lib/cn";

export function Reveal({
  children,
  className,
  delay = 0,
  y = 14,
  ...props
}: MotionProps & {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
}) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const inView = useInView(ref, { margin: "-80px", once: true });

  return (
    <motion.div
      ref={ref}
      className={cn(className)}
      initial={{ opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1], delay }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

