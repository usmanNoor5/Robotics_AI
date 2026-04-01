import { profile } from "@/lib/profile";
import { SectionHeading } from "@/components/ui/section-heading";
import { Badge } from "@/components/ui/badge";

function formatRange(start: string, end: string) {
  return `${start} — ${end}`;
}

export function Journey() {
  const items = [...profile.experience].reverse();

  return (
    <section id="journey" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Journey"
          title="Career timeline"
          subtitle="A clear view of roles and progression across robotics, embedded systems, and computer vision."
        />

        <div className="relative grid gap-4">
          <div className="pointer-events-none absolute left-4 top-0 hidden h-full w-px bg-white/10 sm:block" />
          {items.map((e) => (
            <div
              key={`${e.company}-${e.role}-${e.start}`}
              className="relative rounded-2xl border border-white/10 bg-card/70 p-6 shadow-glow sm:pl-12"
            >
              <div className="absolute left-3 top-7 hidden h-3 w-3 rounded-full border border-white/15 bg-bg sm:block" />
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="font-display text-lg font-semibold tracking-tight">
                    {e.role}
                  </p>
                  <p className="mt-1 text-sm text-fg/70">{e.company}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium tracking-[0.22em] text-muted uppercase">
                    {formatRange(e.start, e.end)}
                  </p>
                  {e.location ? (
                    <p className="mt-2 text-xs text-fg/60">{e.location}</p>
                  ) : null}
                </div>
              </div>
              {e.highlights.length ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {e.highlights.slice(0, 3).map((h) => (
                    <Badge key={h} className="text-fg/70">
                      {h}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-fg/60">
                  Highlights will be expanded as projects are published.
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

