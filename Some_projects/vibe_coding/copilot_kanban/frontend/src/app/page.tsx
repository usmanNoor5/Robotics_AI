"use client";

import { useMemo, useState } from "react";
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
  DraggableLocation,
} from "@hello-pangea/dnd";
import type { Board, Column, Card } from "@/types/kanban";

const COLOR = {
  background: "#eaf2ff",
  card: "#ffffff",
  border: "#d4dbe5",
  text: "#032147",
  secondaryText: "#888888",
  accent: "#ecad0a",
  primary: "#209dd7",
  secondaryButton: "#753991",
};

const initialBoard: Board = {
  columns: [
    {
      id: "col-1",
      title: "Backlog",
      cards: [
        { id: "card-1", title: "Design login flow", details: "Create wireframes and user journey" },
      ],
    },
    {
      id: "col-2",
      title: "To Do",
      cards: [
        { id: "card-2", title: "Set up project scaffold", details: "Next.js + TypeScript + Tailwind" },
      ],
    },
    {
      id: "col-3",
      title: "In Progress",
      cards: [
        { id: "card-3", title: "Implement drag & drop", details: "Use @hello-pangea/dnd" },
      ],
    },
    {
      id: "col-4",
      title: "Review",
      cards: [
        { id: "card-4", title: "Write tests", details: "Unit + integration" },
      ],
    },
    {
      id: "col-5",
      title: "Done",
      cards: [
        { id: "card-5", title: "Finalize MVP scope", details: "No persistence, one board" },
      ],
    },
  ],
};

function reorderCards(source: Card[], destination: Card[], sourceIndex: number, destinationIndex: number) {
  const sourceClone = [...source];
  const destClone = [...destination];
  const [moved] = sourceClone.splice(sourceIndex, 1);
  destClone.splice(destinationIndex, 0, moved);
  return { source: sourceClone, destination: destClone };
}

export default function Home() {
  const [board, setBoard] = useState<Board>(initialBoard);
  const [editingColumnId, setEditingColumnId] = useState<string | null>(null);
  const [columnTitles, setColumnTitles] = useState<Record<string, string>>(
    Object.fromEntries(initialBoard.columns.map((column) => [column.id, column.title]))
  );
  const [newCardFields, setNewCardFields] = useState<Record<string, { title: string; details: string }>>(
    Object.fromEntries(initialBoard.columns.map((column) => [column.id, { title: "", details: "" }]))
  );

  const onDragEnd = (result: DropResult) => {
    const { source, destination } = result;
    if (!destination) return;

    if (source.droppableId === destination.droppableId && source.index === destination.index) return;

    setBoard((previous) => {
      const newColumns = [...previous.columns];
      const sourceColumn = newColumns.find((col) => col.id === source.droppableId);
      const destinationColumn = newColumns.find((col) => col.id === destination.droppableId);
      if (!sourceColumn || !destinationColumn) return previous;

      if (sourceColumn === destinationColumn) {
        const cards = Array.from(sourceColumn.cards);
        const [movedCard] = cards.splice(source.index, 1);
        cards.splice(destination.index, 0, movedCard);
        const updatedColumn = { ...sourceColumn, cards };
        return {
          columns: newColumns.map((col) => (col.id === updatedColumn.id ? updatedColumn : col)),
        };
      }

      const { source: newSourceCards, destination: newDestinationCards } = reorderCards(
        sourceColumn.cards,
        destinationColumn.cards,
        source.index,
        destination.index
      );

      const updatedSource = { ...sourceColumn, cards: newSourceCards };
      const updatedDestination = { ...destinationColumn, cards: newDestinationCards };

      return {
        columns: newColumns.map((col) => {
          if (col.id === updatedSource.id) return updatedSource;
          if (col.id === updatedDestination.id) return updatedDestination;
          return col;
        }),
      };
    });
  };

  const addCard = (columnId: string) => {
    const payload = newCardFields[columnId];
    if (!payload?.title.trim()) return;

    const newCard: Card = {
      id: `card-${Date.now()}`,
      title: payload.title.trim(),
      details: payload.details.trim(),
    };

    setBoard((previous) => ({
      columns: previous.columns.map((col) =>
        col.id === columnId ? { ...col, cards: [...col.cards, newCard] } : col
      ),
    }));

    setNewCardFields((previous) => ({
      ...previous,
      [columnId]: { title: "", details: "" },
    }));
  };

  const deleteCard = (columnId: string, cardId: string) => {
    setBoard((previous) => ({
      columns: previous.columns.map((col) =>
        col.id === columnId
          ? { ...col, cards: col.cards.filter((card) => card.id !== cardId) }
          : col
      ),
    }));
  };

  const updateColumnTitle = (columnId: string) => {
    const nextTitle = columnTitles[columnId]?.trim();
    if (!nextTitle) return;

    setBoard((previous) => ({
      columns: previous.columns.map((col) =>
        col.id === columnId ? { ...col, title: nextTitle } : col
      ),
    }));
    setEditingColumnId(null);
  };

  const boardSummary = useMemo(() => {
    const totalCards = board.columns.reduce((acc, col) => acc + col.cards.length, 0);
    return `${board.columns.length} columns • ${totalCards} cards`;
  }, [board]);

  return (
    <div className="min-h-screen bg-[#f4f8ff] p-4 text-[#032147]">
      <header className="p-4 rounded-xl border border-[#d4dbe5] bg-white shadow-sm mb-4">
        <h1 className="text-3xl font-bold" style={{ color: COLOR.primary }}>
          Kanban Project Manager
        </h1>
        <p className="text-sm text-[#888888]">Single board, 5 columns, drag and drop</p>
        <p className="mt-2 text-xs font-medium text-[#753991]">{boardSummary}</p>
      </header>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {board.columns.map((column, colIndex) => (
            <Droppable key={column.id} droppableId={column.id}>
              {(provided) => (
                <section
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="rounded-lg border border-[#d4dbe5] bg-white p-3 shadow-sm"
                  style={{ backgroundColor: COLOR.background }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    {editingColumnId === column.id ? (
                      <div className="flex gap-2 w-full">
                        <input
                          value={columnTitles[column.id] ?? column.title}
                          onChange={(event) =>
                            setColumnTitles((prev) => ({ ...prev, [column.id]: event.target.value }))
                          }
                          className="w-full rounded border px-2 py-1"
                          onKeyDown={(event) => {
                            if (event.key === "Enter") updateColumnTitle(column.id);
                          }}
                          aria-label={`Edit column title ${column.title}`}
                        />
                        <button
                          onClick={() => updateColumnTitle(column.id)}
                          className="rounded bg-[#209dd7] px-2 py-1 text-white"
                        >
                          Save
                        </button>
                      </div>
                    ) : (
                      <>
                        <h2 className="text-lg font-semibold" style={{ color: COLOR.text }}>
                          {column.title}
                        </h2>
                        <button
                          className="text-sm font-medium text-[#753991] hover:underline"
                          onClick={() => {
                            setEditingColumnId(column.id);
                            setColumnTitles((prev) => ({ ...prev, [column.id]: column.title }));
                          }}
                        >
                          Rename
                        </button>
                      </>
                    )}
                  </div>

                  <div className="space-y-2">
                    {column.cards.map((card, index) => (
                      <Draggable key={card.id} draggableId={card.id} index={index}>
                        {(dragProvided, snapshot) => (
                          <article
                            ref={dragProvided.innerRef}
                            {...dragProvided.draggableProps}
                            {...dragProvided.dragHandleProps}
                            className="rounded-lg border p-3 bg-white shadow-sm"
                            style={{
                              borderColor: snapshot.isDragging ? COLOR.accent : COLOR.border,
                              ...dragProvided.draggableProps.style,
                            }}
                          >
                            <div className="flex justify-between items-start gap-2">
                              <h3 className="text-sm font-semibold" style={{ color: COLOR.text }}>
                                {card.title}
                              </h3>
                              <button
                                className="text-xs text-[#ff4d6d]"
                                onClick={() => deleteCard(column.id, card.id)}
                                aria-label={`Delete card ${card.title}`}
                              >
                                Delete
                              </button>
                            </div>
                            <p className="mt-1 text-xs text-[#888888]">{card.details}</p>
                          </article>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>

                  <div className="mt-3 space-y-2 rounded p-2 bg-white">
                    <input
                      value={newCardFields[column.id]?.title ?? ""}
                      onChange={(event) =>
                        setNewCardFields((prev) => ({
                          ...prev,
                          [column.id]: { ...prev[column.id], title: event.target.value },
                        }))
                      }
                      className="w-full rounded border px-2 py-1 text-sm"
                      placeholder="Card title"
                      aria-label={`New card title for ${column.title}`}
                    />
                    <textarea
                      rows={2}
                      value={newCardFields[column.id]?.details ?? ""}
                      onChange={(event) =>
                        setNewCardFields((prev) => ({
                          ...prev,
                          [column.id]: { ...prev[column.id], details: event.target.value },
                        }))
                      }
                      className="w-full rounded border px-2 py-1 text-sm"
                      placeholder="Details"
                      aria-label={`New card details for ${column.title}`}
                    />
                    <button
                      onClick={() => addCard(column.id)}
                      className="w-full rounded bg-[#753991] px-2 py-1 text-sm font-semibold text-white hover:bg-[#632f7c]"
                    >
                      + Add Card
                    </button>
                  </div>
                </section>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>

      <footer className="mt-4 text-xs text-[#888888] text-center">
        No persistence: refreshing resets board. This is an MVP implementation.
      </footer>
    </div>
  );
}
