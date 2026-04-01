import { About } from "@/components/sections/about";
import { Contact } from "@/components/sections/contact";
import { Education } from "@/components/sections/education";
import { Experience } from "@/components/sections/experience";
import { Hero } from "@/components/sections/hero";
import { Journey } from "@/components/sections/journey";
import { Nav } from "@/components/sections/nav";
import { Portfolio } from "@/components/sections/portfolio";
import { Skills } from "@/components/sections/skills";

export default function HomePage() {
  return (
    <main>
      <Nav />
      <Hero />
      <About />
      <Journey />
      <Skills />
      <Experience />
      <Education />
      <Portfolio />
      <Contact />
    </main>
  );
}

