import type { BoardColumn, NewCardInput } from "@/lib/types";

export type CardMovement = {
  destinationColumnId: string;
  destinationIndex: number;
  sourceColumnId: string;
  sourceIndex: number;
};

export function normalizeColumnName(name: string, fallback: string) {
  const trimmedName = name.trim();
  return trimmedName || fallback;
}

export function normalizeCardInput(input: NewCardInput) {
  return {
    title: input.title.trim(),
    details: input.details.trim(),
  };
}

export function renameColumn(
  columns: BoardColumn[],
  columnId: string,
  nextName: string,
) {
  return columns.map((column) =>
    column.id === columnId
      ? {
          ...column,
          name: normalizeColumnName(nextName, column.name),
        }
      : column,
  );
}

export function addCard(
  columns: BoardColumn[],
  columnId: string,
  input: NewCardInput,
) {
  const nextCard = normalizeCardInput(input);

  if (!nextCard.title || !nextCard.details) {
    return columns;
  }

  return columns.map((column) =>
    column.id === columnId
      ? {
          ...column,
          cards: [
            ...column.cards,
            {
              id: crypto.randomUUID(),
              title: nextCard.title,
              details: nextCard.details,
            },
          ],
        }
      : column,
  );
}

export function deleteCard(
  columns: BoardColumn[],
  columnId: string,
  cardId: string,
) {
  return columns.map((column) =>
    column.id === columnId
      ? {
          ...column,
          cards: column.cards.filter((card) => card.id !== cardId),
        }
      : column,
  );
}

export function moveCard(columns: BoardColumn[], movement: CardMovement) {
  const {
    destinationColumnId,
    destinationIndex,
    sourceColumnId,
    sourceIndex,
  } = movement;

  if (
    sourceColumnId === destinationColumnId &&
    sourceIndex === destinationIndex
  ) {
    return columns;
  }

  const sourceColumnIndex = columns.findIndex((column) => column.id === sourceColumnId);
  const destinationColumnIndex = columns.findIndex(
    (column) => column.id === destinationColumnId,
  );

  if (sourceColumnIndex === -1 || destinationColumnIndex === -1) {
    return columns;
  }

  const sourceCards = [...columns[sourceColumnIndex].cards];
  const [movedCard] = sourceCards.splice(sourceIndex, 1);

  if (!movedCard) {
    return columns;
  }

  if (sourceColumnIndex === destinationColumnIndex) {
    sourceCards.splice(destinationIndex, 0, movedCard);

    return columns.map((column, index) =>
      index === sourceColumnIndex ? { ...column, cards: sourceCards } : column,
    );
  }

  const destinationCards = [...columns[destinationColumnIndex].cards];
  destinationCards.splice(destinationIndex, 0, movedCard);

  return columns.map((column, index) => {
    if (index === sourceColumnIndex) {
      return { ...column, cards: sourceCards };
    }

    if (index === destinationColumnIndex) {
      return { ...column, cards: destinationCards };
    }

    return column;
  });
}
