"use client";

import type { Card } from "@/lib/types";

export default function KanbanCard({
  card,
  onDelete,
}: {
  card: Card;
  onDelete: () => void;
}) {
  return (
    <div data-testid={card.id} className="rounded-lg border border-foreground/10 bg-white p-3 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-navy">{card.title}</h3>
          <p className="mt-1 text-xs leading-relaxed text-gray-text">
            {card.details}
          </p>
        </div>
        <button
          type="button"
          aria-label="Delete card"
          onClick={onDelete}
          onPointerDown={(e) => {
            // Prevent the card wrapper's DnD pointer listeners from intercepting clicks.
            e.stopPropagation();
          }}
          className="rounded-md border border-foreground/10 px-2 py-1 text-xs text-gray-text transition-colors hover:border-accent hover:text-navy"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

