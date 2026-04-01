import { profile } from "@/lib/profile";
import { Reveal } from "@/components/motion/reveal";
import { Badge } from "@/components/ui/badge";
import { SectionHeading } from "@/components/ui/section-heading";

export function About() {
  return (
    <section id="about" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="About"
          title="Engineering intelligence into motion"
          subtitle="I focus on robotics systems where perception, planning, and control meet real deployment constraints."
        />

        <div className="grid gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="rounded-2xl border border-white/10 bg-card/70 p-6 shadow-glow sm:p-7">
              <p className="text-sm leading-relaxed text-fg/75 sm:text-base">
                {profile.summary}
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {profile.topSkills.map((s) => (
                  <Badge
                    key={s}
                    className="border-white/10 bg-white/[0.06] text-fg/80"
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="rounded-2xl border border-white/10 bg-gradient-to-b from-card/70 to-card2/70 p-6 shadow-glow sm:p-7">
              <p className="text-sm font-medium text-fg">Focus areas</p>
              <p className="mt-2 text-sm text-fg/65">
                Tools and domains I work in most often.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {profile.focusAreas.map((t) => (
                  <Badge key={t}>{t}</Badge>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

