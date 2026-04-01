"use client";

import { useState } from "react";
import {
  pointerWithin,
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { KanbanState } from "@/lib/types";
import { addCard, deleteCard, moveCard, renameColumn } from "@/lib/kanbanLogic";
import Column from "./Column";
import SortableKanbanCard from "./SortableKanbanCard";

const initialState: KanbanState = {
  columns: [
    { id: "c1", title: "Todo" },
    { id: "c2", title: "Doing" },
    { id: "c3", title: "Review" },
    { id: "c4", title: "Testing" },
    { id: "c5", title: "Done" },
  ],
  cardsByColumnId: {
    c1: [
      { id: "card-1", title: "Draft roadmap", details: "Outline MVP scope and milestones." },
      { id: "card-2", title: "Design UI", details: "Plan layout, spacing, and color palette usage." },
    ],
    c2: [{ id: "card-3", title: "Implement logic", details: "Add pure kanban functions + unit tests." }],
    c3: [{ id: "card-4", title: "Review components", details: "Validate rename/add/delete UI interactions." }],
    c4: [],
    c5: [{ id: "card-5", title: "Ship MVP", details: "Run E2E checks and finalize the UI polish." }],
  },
};

export default function Board() {
  const [state, setState] = useState<KanbanState>(initialState);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    setState((prev) => {
      const findColumnIdForCard = (cardId: string) =>
        Object.entries(prev.cardsByColumnId).find(([, cards]) =>
          cards.some((c) => c.id === cardId)
        )?.[0] ?? null;

      const sourceColumnId = findColumnIdForCard(activeId);
      if (!sourceColumnId) return prev;

      const sourceCards = prev.cardsByColumnId[sourceColumnId] ?? [];
      const sourceIndex = sourceCards.findIndex((c) => c.id === activeId);
      if (sourceIndex < 0) return prev;

      const overColumnFromCardId = findColumnIdForCard(overId);
      const destinationColumnId = overColumnFromCardId ?? overId;
      const destinationCards =
        prev.cardsByColumnId[destinationColumnId] ?? [];

      const destinationIndex = overColumnFromCardId
        ? destinationCards.findIndex((c) => c.id === overId)
        : destinationCards.length;

      if (destinationIndex < 0) return prev;
      if (
        destinationColumnId === sourceColumnId &&
        destinationIndex === sourceIndex
      ) {
        return prev;
      }

      return moveCard(
        prev,
        sourceColumnId,
        destinationColumnId,
        sourceIndex,
        destinationIndex
      );
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-foreground/10 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-accent" />
          <h1 className="text-lg font-semibold text-navy">Kanban Project Manager</h1>
        </div>
      </header>

             <main className="mx-auto max-w-6xl px-6 py-6">
               <DndContext
                 collisionDetection={pointerWithin}
                 sensors={sensors}
                 onDragEnd={handleDragEnd}
               >
          <div className="flex gap-4 overflow-x-auto pb-2">
            {state.columns.map((column) => {
              const columnCards = state.cardsByColumnId[column.id] ?? [];

              return (
                <SortableContext
                  key={column.id}
                  items={columnCards.map((c) => c.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <Column
                    column={column}
                    cards={columnCards}
                    onRename={(newTitle) =>
                      setState((s) => renameColumn(s, column.id, newTitle))
                    }
                    onAddCard={(input) =>
                      setState((s) => addCard(s, column.id, input))
                    }
                    onDeleteCard={(cardId) =>
                      setState((s) => deleteCard(s, column.id, cardId))
                    }
                  >
                    {columnCards.map((card) => (
                      <SortableKanbanCard
                        key={card.id}
                        card={card}
                        onDelete={() =>
                          setState((s) => deleteCard(s, column.id, card.id))
                        }
                      />
                    ))}
                  </Column>
                </SortableContext>
              );
            })}
          </div>
        </DndContext>
      </main>
    </div>
  );
}

