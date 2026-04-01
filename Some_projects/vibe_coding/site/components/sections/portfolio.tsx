import { Plus } from "lucide-react";

import { SectionHeading } from "@/components/ui/section-heading";
import { Card, CardInner } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const placeholders = [
  {
    title: "Autonomous navigation system",
    desc: "Coming soon — add links, writeups, and demos.",
  },
  {
    title: "Perception + tracking",
    desc: "Coming soon — vision pipelines, datasets, and benchmarks.",
  },
  {
    title: "ROS2 simulation toolkit",
    desc: "Coming soon — packages, docs, and videos.",
  },
] as const;

export function Portfolio() {
  return (
    <section id="portfolio" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Portfolio"
          title="Work, curated"
          subtitle="A clean space ready for future project links and case studies."
        />

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {placeholders.map((p) => (
            <Card key={p.title} className="transition hover:-translate-y-[2px]">
              <CardInner>
                <p className="font-display text-lg font-semibold tracking-tight">
                  {p.title}
                </p>
                <p className="mt-2 text-sm text-fg/65">{p.desc}</p>
                <div className="mt-6 h-px w-full hairline" />
                <Button className="mt-5 w-full" variant="secondary" disabled>
                  Add project <Plus className="h-4 w-4" />
                </Button>
              </CardInner>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

