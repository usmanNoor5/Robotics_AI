import { Link, Mail, Phone } from "lucide-react";

import { profile } from "@/lib/profile";
import { SectionHeading } from "@/components/ui/section-heading";
import { Card, CardInner } from "@/components/ui/card";

export function Contact() {
  return (
    <section id="contact" className="py-14">
      <div className="container">
        <SectionHeading
          kicker="Contact"
          title="Let’s connect"
          subtitle="Open to collaboration, learning, and building robotics systems that matter."
        />

        <Card className="bg-gradient-to-b from-white/[0.06] via-card/70 to-card2/70">
          <CardInner className="grid gap-4 sm:grid-cols-3">
            <a
              className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.08]"
              href={`mailto:${profile.contact.email}`}
            >
              <div className="flex items-center gap-2 text-sm font-medium text-fg">
                <Mail className="h-4 w-4" />
                Email
              </div>
              <p className="mt-2 text-sm text-fg/70">{profile.contact.email}</p>
            </a>

            <a
              className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.08]"
              href={`tel:${profile.contact.phone}`}
            >
              <div className="flex items-center gap-2 text-sm font-medium text-fg">
                <Phone className="h-4 w-4" />
                Phone
              </div>
              <p className="mt-2 text-sm text-fg/70">{profile.contact.phone}</p>
            </a>

            <a
              className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.08]"
              href={profile.contact.linkedin}
              target="_blank"
              rel="noreferrer"
            >
              <div className="flex items-center gap-2 text-sm font-medium text-fg">
                <Link className="h-4 w-4" />
                LinkedIn
              </div>
              <p className="mt-2 text-sm text-fg/70">View profile</p>
            </a>
          </CardInner>
        </Card>

        <p className="mt-6 text-xs text-fg/55">
          © {new Date().getFullYear()} {profile.name}. Built with Next.js.
        </p>
      </div>
    </section>
  );
}

