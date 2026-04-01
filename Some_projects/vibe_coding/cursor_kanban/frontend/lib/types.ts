export type Column = {
  id: string;
  title: string;
};

export type Card = {
  id: string;
  title: string;
  details: string;
};

export type KanbanState = {
  columns: Column[];
  cardsByColumnId: Record<string, Card[]>;
};

