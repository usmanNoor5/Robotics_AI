import type { KanbanState } from "./types";
import {
  addCard,
  deleteCard,
  moveCard,
  renameColumn,
} from "./kanbanLogic";

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
      { id: "card-1", title: "A", details: "alpha" },
      { id: "card-2", title: "B", details: "beta" },
    ],
    c2: [],
    c3: [],
    c4: [],
    c5: [],
  },
};

describe("kanbanLogic", () => {
  test("renameColumn updates the correct column title", () => {
    const next = renameColumn(initialState, "c2", "In Progress");
    const renamed = next.columns.find((c) => c.id === "c2");
    expect(renamed?.title).toBe("In Progress");
  });

  test("addCard appends to the end of the specified column", () => {
    const next = addCard(initialState, "c2", {
      title: "C",
      details: "gamma",
    });

    expect(next.cardsByColumnId.c2).toHaveLength(1);
    expect(next.cardsByColumnId.c2[0]).toEqual({
      id: "card-3",
      title: "C",
      details: "gamma",
    });
  });

  test("deleteCard removes the card by id", () => {
    const next = deleteCard(initialState, "c1", "card-1");
    expect(next.cardsByColumnId.c1.map((c) => c.id)).toEqual(["card-2"]);
  });

  test("moveCard moves a card between columns", () => {
    const next = moveCard(initialState, "c1", "c2", 0, 0);
    expect(next.cardsByColumnId.c1.map((c) => c.id)).toEqual(["card-2"]);
    expect(next.cardsByColumnId.c2.map((c) => c.id)).toEqual(["card-1"]);
  });

  test("moveCard reorders within the same column", () => {
    const next = moveCard(initialState, "c1", "c1", 0, 1);
    expect(next.cardsByColumnId.c1.map((c) => c.id)).toEqual([
      "card-2",
      "card-1",
    ]);
  });
});

