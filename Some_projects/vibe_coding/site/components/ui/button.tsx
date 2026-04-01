import * as React from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const base =
  "inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition will-change-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 disabled:pointer-events-none disabled:opacity-50";

const variants: Record<ButtonVariant, string> = {
  primary:
    "border-white/12 bg-white/[0.10] text-fg shadow-neon hover:bg-white/[0.14] hover:-translate-y-[1px] active:translate-y-0",
  secondary:
    "border-white/12 bg-card/80 text-fg shadow-glow hover:bg-card hover:-translate-y-[1px] active:translate-y-0",
  ghost: "border-transparent bg-transparent text-fg/80 hover:text-fg hover:bg-white/[0.06]",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3",
  md: "h-10 px-4",
  lg: "h-11 px-5 text-[15px]",
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    />
  );
}
