"use client";
/* eslint-disable react-hooks/refs */

import {
  Draggable,
  type DroppableProvided,
} from "@hello-pangea/dnd";
import { GripVertical, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { normalizeCardInput, normalizeColumnName } from "@/lib/board-utils";
import type { BoardColumn, NewCardInput } from "@/lib/types";

type KanbanColumnProps = {
  accent: string;
  column: BoardColumn;
  isDraggingOver: boolean;
  onAddCard: (columnId: string, input: NewCardInput) => void;
  onDeleteCard: (columnId: string, cardId: string) => void;
  onRenameColumn: (columnId: string, name: string) => void;
  provided: DroppableProvided;
};

export function KanbanColumn({
  accent,
  column,
  isDraggingOver,
  onAddCard,
  onDeleteCard,
  onRenameColumn,
  provided,
}: KanbanColumnProps) {
  const [draftName, setDraftName] = useState(column.name);
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftDetails, setDraftDetails] = useState("");

  useEffect(() => {
    setDraftName(column.name);
  }, [column.name]);

  const commitColumnName = () => {
    const nextName = normalizeColumnName(draftName, column.name);
    setDraftName(nextName);
    onRenameColumn(column.id, nextName);
  };

  const handleAddCard = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextCard = normalizeCardInput({
      title: draftTitle,
      details: draftDetails,
    });

    if (!nextCard.title || !nextCard.details) {
      return;
    }

    onAddCard(column.id, nextCard);
    setDraftTitle("");
    setDraftDetails("");
    setIsComposerOpen(false);
  };

  return (
    <section
      className="glass-panel flex w-[21rem] flex-col rounded-[28px] p-4 sm:p-5"
      style={{
        borderColor: isDraggingOver ? `${accent}66` : undefined,
        boxShadow: isDraggingOver
          ? `0 24px 60px ${accent}22`
          : "0 24px 60px rgba(3, 33, 71, 0.12)",
      }}
    >
      <div
        className="mb-4 h-1.5 rounded-full"
        style={{ backgroundColor: accent }}
      />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <label
            className="mb-2 block text-xs font-semibold tracking-[0.18em] text-gray-text uppercase"
            htmlFor={`column-name-${column.id}`}
          >
            Lane Name
          </label>
          <input
            aria-label={`Rename ${column.name} column`}
            className="w-full rounded-2xl border border-transparent bg-white/70 px-3 py-2 font-display text-2xl font-semibold tracking-tight text-dark-navy outline-none transition focus:border-blue-primary/40 focus:bg-white"
            id={`column-name-${column.id}`}
            maxLength={30}
            onBlur={commitColumnName}
            onChange={(event) => setDraftName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.currentTarget.blur();
              }

              if (event.key === "Escape") {
                setDraftName(column.name);
                event.currentTarget.blur();
              }
            }}
            value={draftName}
          />
        </div>

        <div
          className="shrink-0 rounded-full px-3 py-1 text-sm font-semibold"
          style={{
            backgroundColor: `${accent}1A`,
            color: accent,
          }}
        >
          {column.cards.length}
        </div>
      </div>

      <div
        {...provided.droppableProps}
        className={`mt-4 flex min-h-[15rem] flex-1 flex-col gap-3 rounded-[24px] border border-dashed p-3 transition ${
          isDraggingOver
            ? "border-blue-primary/50 bg-blue-primary/6"
            : "border-dark-navy/10 bg-white/50"
        }`}
        data-testid={`column-${column.id}`}
        ref={provided.innerRef}
      >
        {column.cards.length === 0 ? (
          <div className="rounded-[20px] border border-white/80 bg-white/70 px-4 py-5 text-sm leading-6 text-gray-text">
            Drop a card here or create a new one below.
          </div>
        ) : null}

        {column.cards.map((card, index) => (
          <Draggable draggableId={card.id} index={index} key={card.id}>
            {(dragProvided, dragSnapshot) => (
              <article
                className={`rounded-[22px] border border-white/80 bg-white/92 p-4 shadow-[0_16px_28px_rgba(3,33,71,0.08)] transition ${
                  dragSnapshot.isDragging ? "rotate-[1deg] shadow-[0_22px_45px_rgba(3,33,71,0.16)]" : ""
                }`}
                data-testid={`card-${card.id}`}
                ref={dragProvided.innerRef}
                {...dragProvided.draggableProps}
                {...dragProvided.dragHandleProps}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className="mt-0.5 rounded-full p-1.5"
                      style={{ backgroundColor: `${accent}16`, color: accent }}
                    >
                      <GripVertical className="h-4 w-4" />
                    </div>
                    <div className="space-y-2">
                      <h2 className="font-display text-lg font-semibold leading-6 text-dark-navy">
                        {card.title}
                      </h2>
                      <p className="text-sm leading-6 text-gray-text">{card.details}</p>
                    </div>
                  </div>

                  <button
                    aria-label={`Delete ${card.title}`}
                    className="rounded-full p-2 text-gray-text transition hover:bg-dark-navy/5 hover:text-purple-secondary"
                    onClick={() => onDeleteCard(column.id, card.id)}
                    type="button"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </article>
            )}
          </Draggable>
        ))}

        {provided.placeholder}
      </div>

      {isComposerOpen ? (
        <form
          className="mt-4 space-y-3 rounded-[24px] border border-purple-secondary/15 bg-white/80 p-4"
          onSubmit={handleAddCard}
        >
          <div className="space-y-2">
            <label
              className="block text-xs font-semibold tracking-[0.18em] text-gray-text uppercase"
              htmlFor={`card-title-${column.id}`}
            >
              Card Title
            </label>
            <input
              className="w-full rounded-2xl border border-dark-navy/10 bg-white px-3 py-2.5 text-sm text-dark-navy outline-none transition focus:border-blue-primary/40"
              id={`card-title-${column.id}`}
              maxLength={80}
              onChange={(event) => setDraftTitle(event.target.value)}
              placeholder="Write a crisp headline"
              required
              value={draftTitle}
            />
          </div>

          <div className="space-y-2">
            <label
              className="block text-xs font-semibold tracking-[0.18em] text-gray-text uppercase"
              htmlFor={`card-details-${column.id}`}
            >
              Card Details
            </label>
            <textarea
              className="min-h-28 w-full resize-none rounded-2xl border border-dark-navy/10 bg-white px-3 py-2.5 text-sm leading-6 text-dark-navy outline-none transition focus:border-blue-primary/40"
              id={`card-details-${column.id}`}
              maxLength={220}
              onChange={(event) => setDraftDetails(event.target.value)}
              placeholder="Add just enough context for the next handoff"
              required
              value={draftDetails}
            />
          </div>

          <div className="flex gap-2">
            <button
              className="inline-flex items-center justify-center rounded-full bg-purple-secondary px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-110"
              type="submit"
            >
              Create Card
            </button>
            <button
              className="inline-flex items-center justify-center rounded-full border border-dark-navy/10 px-4 py-2.5 text-sm font-semibold text-dark-navy transition hover:bg-dark-navy/5"
              onClick={() => {
                setDraftTitle("");
                setDraftDetails("");
                setIsComposerOpen(false);
              }}
              type="button"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          className="mt-4 inline-flex items-center justify-center gap-2 rounded-full border border-dark-navy/10 bg-white/80 px-4 py-3 text-sm font-semibold text-dark-navy transition hover:border-blue-primary/30 hover:bg-white hover:text-blue-primary"
          onClick={() => setIsComposerOpen(true)}
          type="button"
        >
          <Plus className="h-4 w-4" />
          Add Card
        </button>
      )}
    </section>
  );
}
