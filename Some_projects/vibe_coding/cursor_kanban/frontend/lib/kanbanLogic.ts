import type { Card, KanbanState } from "./types";

export type NewCardInput = Pick<Card, "title" | "details">;

const totalCards = (state: KanbanState) =>
  Object.values(state.cardsByColumnId).reduce(
    (sum, cards) => sum + cards.length,
    0
  );

export function renameColumn(
  state: KanbanState,
  columnId: string,
  newTitle: string
): KanbanState {
  return {
    ...state,
    columns: state.columns.map((col) =>
      col.id === columnId ? { ...col, title: newTitle } : col
    ),
  };
}

export function addCard(
  state: KanbanState,
  columnId: string,
  input: NewCardInput
): KanbanState {
  if (!state.cardsByColumnId[columnId]) return state;

  const id = `card-${totalCards(state) + 1}`;
  const newCard: Card = {
    id,
    title: input.title,
    details: input.details,
  };

  return {
    ...state,
    cardsByColumnId: {
      ...state.cardsByColumnId,
      [columnId]: [...state.cardsByColumnId[columnId], newCard],
    },
  };
}

export function deleteCard(
  state: KanbanState,
  columnId: string,
  cardId: string
): KanbanState {
  const cards = state.cardsByColumnId[columnId];
  if (!cards) return state;

  return {
    ...state,
    cardsByColumnId: {
      ...state.cardsByColumnId,
      [columnId]: cards.filter((c) => c.id !== cardId),
    },
  };
}

export function moveCard(
  state: KanbanState,
  sourceColumnId: string,
  destinationColumnId: string,
  sourceIndex: number,
  destinationIndex: number
): KanbanState {
  const sourceCards = state.cardsByColumnId[sourceColumnId];
  const destinationCards = state.cardsByColumnId[destinationColumnId];

  if (!sourceCards || !destinationCards) return state;
  const card = sourceCards[sourceIndex];
  if (!card) return state;

  // Move within the same column: remove then insert into the same array.
  if (sourceColumnId === destinationColumnId) {
    const next = [...sourceCards];
    next.splice(sourceIndex, 1);
    const idx = Math.max(0, Math.min(destinationIndex, next.length));
    next.splice(idx, 0, card);

    return {
      ...state,
      cardsByColumnId: {
        ...state.cardsByColumnId,
        [sourceColumnId]: next,
      },
    };
  }

  const nextSource = [...sourceCards];
  nextSource.splice(sourceIndex, 1);

  const nextDestination = [...destinationCards];
  const idx = Math.max(0, Math.min(destinationIndex, nextDestination.length));
  nextDestination.splice(idx, 0, card);

  return {
    ...state,
    cardsByColumnId: {
      ...state.cardsByColumnId,
      [sourceColumnId]: nextSource,
      [destinationColumnId]: nextDestination,
    },
  };
}

