import { cn } from "@/lib/cn";

export function SectionHeading({
  kicker,
  title,
  subtitle,
  className,
}: {
  kicker?: string;
  title: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <div className={cn("mb-8", className)}>
      {kicker ? (
        <p className="text-xs font-medium tracking-[0.22em] text-muted uppercase">
          {kicker}
        </p>
      ) : null}
      <h2 className="mt-3 font-display text-2xl font-semibold tracking-tight sm:text-3xl">
        {title}
      </h2>
      {subtitle ? (
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-fg/70 sm:text-base">
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}

