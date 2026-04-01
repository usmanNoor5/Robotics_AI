import { ArrowRight, Code2, Link, Mail, Phone } from "lucide-react";

import { profile } from "@/lib/profile";
import { Reveal } from "@/components/motion/reveal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardInner } from "@/components/ui/card";

export function Hero() {
  return (
    <section id="top" className="pb-8 pt-12 sm:pt-16">
      <div className="container">
        <div className="grid items-stretch gap-6 lg:grid-cols-[1.25fr_0.75fr]">
          <Reveal>
            <Card className="bg-gradient-to-b from-white/[0.06] via-card/70 to-card2/70">
              <CardInner className="relative">
                <div className="absolute inset-0 opacity-[0.18] [background:radial-gradient(600px_300px_at_30%_0%,rgba(124,92,255,0.55),transparent_55%),radial-gradient(700px_350px_at_90%_30%,rgba(104,255,167,0.45),transparent_60%)]" />
                <div className="relative">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="border-white/10 bg-white/[0.05] text-fg/80">
                      {profile.location}
                    </Badge>
                    <Badge className="text-fg/70">{profile.topSkills[0]}</Badge>
                    <Badge className="text-fg/70">{profile.topSkills[1]}</Badge>
                  </div>

                  <h1 className="mt-6 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
                    {profile.name}
                  </h1>
                  <p className="mt-4 max-w-2xl text-base leading-relaxed text-fg/80 sm:text-lg">
                    {profile.headline}. Building full‑stack robotics systems across
                    perception, planning, and deployment.
                  </p>

                  <div className="mt-7 flex flex-wrap items-center gap-3">
                    <a href="#contact">
                      <Button size="lg">
                        Contact <ArrowRight className="h-4 w-4" />
                      </Button>
                    </a>
                    <a href="#journey">
                      <Button variant="secondary" size="lg">
                        Career journey
                      </Button>
                    </a>
                  </div>

                  <div className="mt-8 h-px w-full hairline" />

                  <div className="mt-6 flex flex-wrap items-center gap-2 text-sm text-fg/80">
                    <a
                      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 transition hover:bg-white/[0.08]"
                      href={`mailto:${profile.contact.email}`}
                    >
                      <Mail className="h-4 w-4" />
                      {profile.contact.email}
                    </a>
                    <a
                      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 transition hover:bg-white/[0.08]"
                      href={`tel:${profile.contact.phone}`}
                    >
                      <Phone className="h-4 w-4" />
                      {profile.contact.phone}
                    </a>
                    <a
                      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 transition hover:bg-white/[0.08]"
                      href={profile.contact.linkedin}
                      target="_blank"
                      rel="noreferrer"
                    >
                    <Link className="h-4 w-4" />
                      LinkedIn
                    </a>
                  </div>
                </div>
              </CardInner>
            </Card>
          </Reveal>

          <Reveal delay={0.08}>
            <Card>
              <CardInner>
                <p className="text-xs font-medium tracking-[0.22em] text-muted uppercase">
                  Profile snapshot
                </p>
                <p className="mt-4 text-sm leading-relaxed text-fg/70">
                  {profile.summary}
                </p>
                <div className="mt-6 flex flex-wrap gap-2">
                  {profile.focusAreas.slice(0, 4).map((t) => (
                    <Badge key={t}>{t}</Badge>
                  ))}
                </div>
                <div className="mt-7 h-px w-full hairline" />
                <div className="mt-6 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-fg">Code & projects</p>
                    <p className="mt-1 text-xs text-fg/65">
                      Portfolio section is ready for future links.
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" disabled>
                    <Code2 className="h-4 w-4" />
                    Coming soon
                  </Button>
                </div>
              </CardInner>
            </Card>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

