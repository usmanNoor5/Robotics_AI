import type { BoardColumn } from "@/lib/types";

export const initialBoardColumns: BoardColumn[] = [
  {
    id: "strategy",
    name: "Strategy",
    cards: [
      {
        id: "card-roadmap",
        title: "Finalize Q2 roadmap",
        details: "Tighten the milestone story before tomorrow's leadership sync.",
      },
      {
        id: "card-narrative",
        title: "Shape robotics demo narrative",
        details: "Align the voiceover beats with the live handoff moments.",
      },
    ],
  },
  {
    id: "in-motion",
    name: "In Motion",
    cards: [
      {
        id: "card-usability",
        title: "Run usability pass",
        details: "Watch three dry-runs and note friction in the board flow.",
      },
      {
        id: "card-copy",
        title: "Tune interface copy",
        details: "Trim labels so every action reads quickly under pressure.",
      },
    ],
  },
  {
    id: "design-review",
    name: "Design Review",
    cards: [
      {
        id: "card-empty-state",
        title: "Refine empty state rhythm",
        details: "Make quiet columns still feel intentional and premium.",
      },
    ],
  },
  {
    id: "build-queue",
    name: "Build Queue",
    cards: [
      {
        id: "card-drag",
        title: "Wire drag interactions",
        details: "Keep transitions buttery while preserving simple behavior.",
      },
      {
        id: "card-spacing",
        title: "Balance card spacing",
        details: "Tune padding and density for a calmer reading experience.",
      },
    ],
  },
  {
    id: "ready-to-launch",
    name: "Ready to Launch",
    cards: [
      {
        id: "card-walkthrough",
        title: "Prep stakeholder walkthrough",
        details: "Queue the crisp path that shows rename, add, delete, and move.",
      },
    ],
  },
];
