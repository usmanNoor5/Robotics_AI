"use client";

import { useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { Card, Column as ColumnType } from "@/lib/types";
import AddCardForm from "./AddCardForm";
import KanbanCard from "./KanbanCard";

export default function Column({
  column,
  cards,
  onRename,
  onAddCard,
  onDeleteCard,
  children,
}: {
  column: ColumnType;
  cards: Card[];
  onRename: (newTitle: string) => void;
  onAddCard: (input: { title: string; details: string }) => void;
  onDeleteCard: (cardId: string) => void;
  children?: ReactNode;
}) {
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(column.title);
  const { setNodeRef } = useDroppable({ id: column.id });

  return (
    <section
      ref={setNodeRef}
      data-testid={`column-${column.id}`}
      className="flex min-w-[240px] flex-col rounded-xl border border-foreground/10 bg-white p-4 shadow-sm"
    >
      <div className="flex items-center justify-between gap-2">
        {!editing ? (
          <button
            type="button"
            onClick={() => {
              setDraftTitle(column.title);
              setEditing(true);
            }}
            className="truncate text-left text-sm font-semibold text-navy hover:underline"
          >
            {column.title}
          </button>
        ) : (
          <input
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                (e.currentTarget as HTMLInputElement).blur();
              }
            }}
            onBlur={() => {
              setEditing(false);
              const next = draftTitle.trim().length > 0 ? draftTitle : column.title;
              onRename(next);
            }}
            autoFocus
            className="w-full rounded-md border border-foreground/10 bg-white px-2 py-1 text-sm font-semibold text-navy outline-none focus:border-accent"
          />
        )}
      </div>

      <div className="mt-3 space-y-3">
        {children ??
          cards.map((card) => (
            <KanbanCard
              key={card.id}
              card={card}
              onDelete={() => onDeleteCard(card.id)}
            />
          ))}
      </div>

      <AddCardForm
        onAdd={(input) => {
          onAddCard(input);
        }}
      />
    </section>
  );
}

