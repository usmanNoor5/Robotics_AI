import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/kanban-board";

vi.mock("@hello-pangea/dnd", async () => {
  const React = await import("react");

  return {
    DragDropContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Droppable: ({
      children,
      droppableId,
    }: {
      children: (provided: {
        innerRef: () => void;
        droppableProps: Record<string, string>;
        placeholder: null;
      }, snapshot: { isDraggingOver: boolean }) => React.ReactNode;
      droppableId: string;
    }) =>
      children({
        innerRef: () => {},
        droppableProps: { "data-droppable-id": droppableId },
        placeholder: null,
      }, { isDraggingOver: false }),
    Draggable: ({
      children,
      draggableId,
    }: {
      children: (provided: {
        innerRef: () => void;
        draggableProps: Record<string, string>;
        dragHandleProps: Record<string, string>;
      }, snapshot: { isDragging: boolean }) => React.ReactNode;
      draggableId: string;
    }) =>
      children(
        {
          innerRef: () => {},
          draggableProps: { "data-draggable-id": draggableId },
          dragHandleProps: { tabIndex: "0" },
        },
        { isDragging: false },
      ),
  };
});

describe("KanbanBoard", () => {
  it("renders the seeded board", () => {
    render(<KanbanBoard />);

    expect(screen.getByRole("heading", { name: "Aurora Sprint Board" })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Strategy")).toBeInTheDocument();
    expect(screen.getByText("Finalize Q2 roadmap")).toBeInTheDocument();
  });

  it("renames a column, adds a card, and deletes it", async () => {
    const user = userEvent.setup();

    render(<KanbanBoard />);

    const strategyColumn = screen.getByTestId("column-strategy");
    const strategySection = strategyColumn.closest("section");
    const renameInput = screen.getByLabelText("Rename Strategy column");

    await user.clear(renameInput);
    await user.type(renameInput, "Concept Lab");
    await user.tab();

    expect(screen.getByDisplayValue("Concept Lab")).toBeInTheDocument();

    expect(strategySection).not.toBeNull();

    await user.click(
      within(strategySection as HTMLElement).getByRole("button", { name: /add card/i }),
    );
    await user.type(screen.getByLabelText("Card Title"), "Confirm robotics keynote");
    await user.type(
      screen.getByLabelText("Card Details"),
      "Lock the final order for the walkthrough sequence.",
    );
    await user.click(screen.getByRole("button", { name: "Create Card" }));

    expect(within(strategyColumn).getByText("Confirm robotics keynote")).toBeInTheDocument();

    await user.click(
      within(strategyColumn).getByRole("button", {
        name: "Delete Confirm robotics keynote",
      }),
    );

    expect(
      within(strategyColumn).queryByText("Confirm robotics keynote"),
    ).not.toBeInTheDocument();
  });
});
