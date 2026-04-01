import { profile } from "@/lib/profile";
import { Reveal } from "@/components/motion/reveal";
import { SectionHeading } from "@/components/ui/section-heading";
import { Card, CardInner } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const groups = [
  {
    title: "Robotics",
    items: ["ROS2", "SLAM", "A*", "Sensor fusion", "Gazebo", "RViz", "MoveIt 2"],
  },
  {
    title: "Perception",
    items: ["YOLOv8", "OpenCV", "Object tracking", "Stereo depth", "RealSense D435i"],
  },
  {
    title: "Hardware + Systems",
    items: ["Jetson Nano/Orin", "Pixhawk", "LiDAR", "Embedded optimization", "Linux"],
  },
  {
    title: "ML + GenAI",
    items: ["TensorFlow", "scikit-learn", "Optimization", "LLMs", "Transformers", "Prompt engineering"],
  },
  {
    title: "Languages",
    items: ["Python", "C++", "Flutter/Dart"],
  },
] as const;

export function Skills() {
  return (
    <section id="skills" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Skills"
          title="Tooling that ships"
          subtitle="A pragmatic stack for building robotics systems end-to-end."
        />

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {groups.map((g, idx) => (
            <Reveal key={g.title} delay={idx * 0.04}>
              <Card>
                <CardInner>
                  <p className="font-display text-lg font-semibold tracking-tight">
                    {g.title}
                  </p>
                  <p className="mt-2 text-sm text-fg/60">
                    {g.title === "ML + GenAI"
                      ? "Exploring real-world GenAI workflows for robotics behavior."
                      : "Battle-tested tools, tuned for deployment constraints."}
                  </p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {g.items.map((i) => (
                      <Badge key={i}>{i}</Badge>
                    ))}
                  </div>
                </CardInner>
              </Card>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.12}>
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-6 shadow-glow sm:p-7">
            <p className="text-sm font-medium text-fg">From your profile</p>
            <p className="mt-2 text-sm text-fg/70">
              {profile.focusAreas.join(" • ")}
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

