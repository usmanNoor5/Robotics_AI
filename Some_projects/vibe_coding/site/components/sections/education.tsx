import { profile } from "@/lib/profile";
import { SectionHeading } from "@/components/ui/section-heading";
import { Card, CardInner } from "@/components/ui/card";

export function Education() {
  return (
    <section id="education" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Education"
          title="Foundations"
          subtitle="Formal training that supports research-minded engineering and real-world delivery."
        />

        <div className="grid gap-5 md:grid-cols-2">
          {profile.education.map((e) => (
            <Card key={e.school}>
              <CardInner>
                <p className="font-display text-lg font-semibold tracking-tight">
                  {e.school}
                </p>
                <p className="mt-2 text-sm text-fg/70">
                  {e.degree}
                  {e.field ? ` • ${e.field}` : ""}
                </p>
                <p className="mt-3 text-xs font-medium tracking-[0.22em] text-muted uppercase">
                  {e.start} — {e.end}
                </p>
              </CardInner>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

