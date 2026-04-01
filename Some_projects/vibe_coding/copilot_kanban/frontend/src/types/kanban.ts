export interface Card {
  id: string;
  title: string;
  details: string;
}

export interface Column {
  id: string;
  title: string;
  cards: Card[];
}

export interface Board {
  columns: Column[];
}
