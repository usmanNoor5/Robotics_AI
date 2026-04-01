import Link from "next/link";

import { cn } from "@/lib/cn";

const links = [
  { href: "#about", label: "About" },
  { href: "#journey", label: "Journey" },
  { href: "#skills", label: "Skills" },
  { href: "#experience", label: "Experience" },
  { href: "#education", label: "Education" },
  { href: "#portfolio", label: "Portfolio" },
  { href: "#contact", label: "Contact" },
] as const;

export function Nav({ className }: { className?: string }) {
  return (
    <div className={cn("sticky top-4 z-50", className)}>
      <div className="container">
        <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-black/40 px-4 py-3 backdrop-blur">
          <Link
            href="#top"
            className="font-display text-sm font-semibold tracking-tight text-fg"
          >
            MUN
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="rounded-xl px-3 py-2 text-xs font-medium text-fg/70 transition hover:bg-white/[0.06] hover:text-fg"
              >
                {l.label}
              </a>
            ))}
          </nav>
          <a
            href="#contact"
            className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-xs font-medium text-fg/90 transition hover:bg-white/[0.10]"
          >
            Let’s connect
          </a>
        </div>
      </div>
    </div>
  );
}

