export type BoardCard = {
  details: string;
  id: string;
  title: string;
};

export type BoardColumn = {
  cards: BoardCard[];
  id: string;
  name: string;
};

export type NewCardInput = {
  details: string;
  title: string;
};
