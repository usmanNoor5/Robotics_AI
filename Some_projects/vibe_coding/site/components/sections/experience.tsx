import { profile } from "@/lib/profile";
import { SectionHeading } from "@/components/ui/section-heading";
import { Card, CardInner } from "@/components/ui/card";

export function Experience() {
  return (
    <section id="experience" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Experience"
          title="Where I’ve built"
          subtitle="Hands-on roles across robotics simulation, embedded systems, and computer vision."
        />

        <div className="grid gap-5">
          {profile.experience.map((e) => (
            <Card key={`${e.company}-${e.role}-${e.start}`}>
              <CardInner>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="font-display text-lg font-semibold tracking-tight">
                      {e.role}
                    </p>
                    <p className="mt-1 text-sm text-fg/70">{e.company}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium tracking-[0.22em] text-muted uppercase">
                      {e.start} — {e.end}
                    </p>
                    {e.location ? (
                      <p className="mt-2 text-xs text-fg/60">{e.location}</p>
                    ) : null}
                  </div>
                </div>

                {e.highlights.length ? (
                  <ul className="mt-5 list-disc space-y-2 pl-5 text-sm text-fg/70">
                    {e.highlights.map((h) => (
                      <li key={h}>{h}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-5 text-sm text-fg/60">
                    Highlights coming soon (this is a great place to add project
                    links as you publish them).
                  </p>
                )}
              </CardInner>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

