"use client";

import { DragDropContext, Droppable, type DropResult } from "@hello-pangea/dnd";
import { ArrowRight, LayoutPanelTop, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import { KanbanColumn } from "@/components/kanban-column";
import { initialBoardColumns } from "@/lib/board-data";
import { addCard, deleteCard, moveCard, renameColumn } from "@/lib/board-utils";
import type { NewCardInput } from "@/lib/types";

const columnAccents = [
  "#209dd7",
  "#ecad0a",
  "#753991",
  "#032147",
  "#209dd7",
];

export function KanbanBoard() {
  const [columns, setColumns] = useState(initialBoardColumns);

  const totalCards = columns.reduce((count, column) => count + column.cards.length, 0);

  const handleRenameColumn = (columnId: string, name: string) => {
    setColumns((currentColumns) => renameColumn(currentColumns, columnId, name));
  };

  const handleAddCard = (columnId: string, input: NewCardInput) => {
    setColumns((currentColumns) => addCard(currentColumns, columnId, input));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setColumns((currentColumns) => deleteCard(currentColumns, columnId, cardId));
  };

  const handleDragEnd = (result: DropResult) => {
    const destination = result.destination;

    if (!destination) {
      return;
    }

    setColumns((currentColumns) =>
      moveCard(currentColumns, {
        sourceColumnId: result.source.droppableId,
        destinationColumnId: destination.droppableId,
        sourceIndex: result.source.index,
        destinationIndex: destination.index,
      }),
    );
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-8rem] top-10 h-72 w-72 rounded-full bg-blue-primary/15 blur-3xl" />
        <div className="absolute right-[-6rem] top-18 h-64 w-64 rounded-full bg-purple-secondary/15 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-accent-yellow/15 blur-3xl" />
      </div>

      <main className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col gap-8 px-4 py-5 sm:px-6 sm:py-6 lg:px-10 lg:py-8">
        <section className="glass-panel rounded-[30px] px-5 py-6 sm:px-7 sm:py-7 lg:px-8 lg:py-8">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-primary/15 bg-white/70 px-4 py-2 text-sm font-semibold tracking-[0.18em] text-blue-primary uppercase">
                <Sparkles className="h-4 w-4" />
                One Board MVP
              </div>

              <div className="space-y-3">
                <h1 className="font-display text-4xl font-bold tracking-tight text-dark-navy sm:text-5xl">
                  Aurora Sprint Board
                </h1>
                <p className="max-w-2xl text-base leading-7 text-gray-text sm:text-lg">
                  A single polished board for the team&apos;s current work. Rename any
                  lane, move cards fluidly across the flow, and keep every decision
                  visible without adding extra process.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-[24px] border border-white/70 bg-white/75 px-4 py-4 shadow-[0_18px_36px_rgba(3,33,71,0.08)]">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-text">
                  <LayoutPanelTop className="h-4 w-4 text-blue-primary" />
                  Fixed Columns
                </div>
                <p className="mt-3 font-display text-3xl font-semibold text-dark-navy">5</p>
              </div>

              <div className="rounded-[24px] border border-white/70 bg-white/75 px-4 py-4 shadow-[0_18px_36px_rgba(3,33,71,0.08)]">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-text">
                  <Zap className="h-4 w-4 text-accent-yellow" />
                  Live Cards
                </div>
                <p className="mt-3 font-display text-3xl font-semibold text-dark-navy">
                  {totalCards}
                </p>
              </div>

              <div className="rounded-[24px] border border-white/70 bg-white/75 px-4 py-4 shadow-[0_18px_36px_rgba(3,33,71,0.08)]">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-text">
                  <ArrowRight className="h-4 w-4 text-purple-secondary" />
                  Interaction
                </div>
                <p className="mt-3 font-display text-xl font-semibold text-dark-navy">
                  Drag, rename, add
                </p>
              </div>
            </div>
          </div>
        </section>

        <DragDropContext onDragEnd={handleDragEnd}>
          <section aria-label="Kanban board" className="overflow-x-auto pb-6">
            <div className="flex min-w-max gap-5">
              {columns.map((column, index) => (
                <Droppable droppableId={column.id} key={column.id}>
                  {(provided, snapshot) => (
                    <KanbanColumn
                      accent={columnAccents[index % columnAccents.length]}
                      column={column}
                      isDraggingOver={snapshot.isDraggingOver}
                      onAddCard={handleAddCard}
                      onDeleteCard={handleDeleteCard}
                      onRenameColumn={handleRenameColumn}
                      provided={provided}
                    />
                  )}
                </Droppable>
              ))}
            </div>
          </section>
        </DragDropContext>
      </main>
    </div>
  );
}
