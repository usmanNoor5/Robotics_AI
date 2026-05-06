# Research Workflow & Paper Reading Instructions (VLA / Robotics / Embodied AI)

> IMPORTANT:
> Your primary job is **research, understanding, organization, and documentation** — NOT coding.
> We are working in the domain of:
>
> - Vision Language Action (VLA)
> - Robotics
> - Embodied AI
> - Humanoid Robotics
> - Robot Learning
> - Manipulation
> - Navigation
> - Reinforcement Learning
> - Foundation Models for Robotics
>
> So the focus should always remain on:
>
> - Understanding research deeply
> - Comparing methods
> - Organizing knowledge
> - Extracting implementation insights
> - Finding limitations and future directions
> - Collecting useful repositories/models/datasets
>
> NOT writing unnecessary code.

---

# VERY IMPORTANT RULES

## 1. DO NOT RANDOMLY ADD THINGS

Before adding:

- GitHub links
- Model links
- HuggingFace links
- Papers
- Repositories
- Datasets
- Benchmarks
- Simulators
- APIs
- citations

YOU MUST FIRST ASK ME TO VERIFY:

- Whether the link works
- Whether the repository is maintained
- Whether it is deprecated
- Whether we should include it
- Whether it aligns with our current VLA direction

DO NOT assume anything yourself.

A lot of robotics/VLA research becomes outdated very quickly.

---

# 2. PRIORITIZE LATEST RESEARCH

Focus mostly on:

- 2025 papers
- 2026 papers

Older papers should ONLY be included if they are:

- foundational
- highly influential
- repeatedly cited
- still actively used

Examples:

- RT-1
- RT-2
- OpenVLA
- π0 / π0.5 style models
- ACT
- Diffusion Policy
- GR00T
- LeRobot
- Mobile ALOHA
- Octo
- Open X-Embodiment

etc.

---

# 3. EVERY PAPER MUST BE SAVED AS A MARKDOWN FILE

Every research paper MUST have:

```text
research/
    paper_name/
        summary.md
        respective_pdf