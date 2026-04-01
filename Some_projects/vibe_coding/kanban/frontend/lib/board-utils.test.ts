import { initialBoardColumns } from "@/lib/board-data";
import {
  addCard,
  deleteCard,
  moveCard,
  normalizeCardInput,
  normalizeColumnName,
  renameColumn,
} from "@/lib/board-utils";

describe("board-utils", () => {
  it("normalizes column names with a fallback", () => {
    expect(normalizeColumnName("  Momentum  ", "Strategy")).toBe("Momentum");
    expect(normalizeColumnName("   ", "Strategy")).toBe("Strategy");
  });

  it("normalizes card input", () => {
    expect(
      normalizeCardInput({
        title: "  Ship update  ",
        details: "  Share the latest interaction notes.  ",
      }),
    ).toEqual({
      title: "Ship update",
      details: "Share the latest interaction notes.",
    });
  });

  it("renames a target column", () => {
    const result = renameColumn(initialBoardColumns, "strategy", "  Concept Lab ");
    expect(result[0].name).toBe("Concept Lab");
    expect(result[1].name).toBe(initialBoardColumns[1].name);
  });

  it("adds a card to the selected column", () => {
    const result = addCard(initialBoardColumns, "strategy", {
      title: "  Confirm keynote sequence  ",
      details: "  Lock the final handoff order for the demo.  ",
    });

    expect(result[0].cards).toHaveLength(initialBoardColumns[0].cards.length + 1);
    expect(result[0].cards.at(-1)).toMatchObject({
      title: "Confirm keynote sequence",
      details: "Lock the final handoff order for the demo.",
    });
  });

  it("does not add incomplete cards", () => {
    const result = addCard(initialBoardColumns, "strategy", {
      title: "Only a title",
      details: "   ",
    });

    expect(result).toEqual(initialBoardColumns);
  });

  it("deletes a targeted card", () => {
    const result = deleteCard(initialBoardColumns, "strategy", "card-roadmap");
    expect(result[0].cards).toHaveLength(initialBoardColumns[0].cards.length - 1);
    expect(result[0].cards.find((card) => card.id === "card-roadmap")).toBeUndefined();
  });

  it("reorders cards inside the same column", () => {
    const result = moveCard(initialBoardColumns, {
      sourceColumnId: "strategy",
      destinationColumnId: "strategy",
      sourceIndex: 0,
      destinationIndex: 1,
    });

    expect(result[0].cards.map((card) => card.id)).toEqual([
      "card-narrative",
      "card-roadmap",
    ]);
  });

  it("moves cards across columns", () => {
    const result = moveCard(initialBoardColumns, {
      sourceColumnId: "strategy",
      destinationColumnId: "in-motion",
      sourceIndex: 0,
      destinationIndex: 1,
    });

    expect(result[0].cards.map((card) => card.id)).toEqual(["card-narrative"]);
    expect(result[1].cards.map((card) => card.id)).toEqual([
      "card-usability",
      "card-roadmap",
      "card-copy",
    ]);
  });
});
