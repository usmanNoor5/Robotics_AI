import { test, expect } from "@playwright/test";

test.describe("Kanban board MVP", () => {
  test("loads 5 columns and dummy cards", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("column-c1")).toBeVisible();
    await expect(page.getByTestId("column-c2")).toBeVisible();
    await expect(page.getByTestId("column-c3")).toBeVisible();
    await expect(page.getByTestId("column-c4")).toBeVisible();
    await expect(page.getByTestId("column-c5")).toBeVisible();

    const totalCards = await page.locator('[data-testid^="card-"]').count();
    expect(totalCards).toBe(5);
  });

  test("can rename a column", async ({ page }) => {
    await page.goto("/");

    const c1Section = page.getByTestId("column-c1");

    await c1Section.getByRole("button", { name: "Todo" }).click();
    const input = c1Section.locator("input").first();
    await expect(input).toBeVisible();
    await input.fill("Backlog");
    await input.press("Enter");

    await expect(c1Section.getByRole("button", { name: "Backlog" })).toBeVisible();
  });

  test("can add a card to a column", async ({ page }) => {
    await page.goto("/");

    const c2Section = page.getByTestId("column-c2");
    const before = await c2Section.locator('[data-testid^="card-"]').count();

    await c2Section.getByRole("button", { name: "+ Add card" }).click();
    await expect(c2Section.getByPlaceholder("Card title")).toBeVisible();
    await c2Section.getByPlaceholder("Card title").fill("New task");
    await c2Section.getByPlaceholder("Card details").fill("Some details");
    await c2Section.getByRole("button", { name: "Add", exact: true }).click();

    await expect(c2Section.locator('[data-testid^="card-"]')).toHaveCount(
      before + 1
    );
  });

  test("can delete a card from a column", async ({ page }) => {
    await page.goto("/");

    const c1Section = page.getByTestId("column-c1");
    const before = await c1Section.locator('[data-testid^="card-"]').count();

    await page.getByTestId("card-1").getByRole("button", { name: "Delete card" }).click();

    await expect(c1Section.locator('[data-testid^="card-"]')).toHaveCount(
      before - 1
    );
  });

  test("can drag a card between columns", async ({ page }) => {
    await page.goto("/");

    const c1Section = page.getByTestId("column-c1");
    const c2Section = page.getByTestId("column-c2");

    const c1Before = await c1Section.locator('[data-testid^="card-"]').count();
    const c2Before = await c2Section.locator('[data-testid^="card-"]').count();
    expect(c1Before).toBe(2);
    expect(c2Before).toBe(1);

    const draggedCard = page.getByTestId("card-1");
    await draggedCard.scrollIntoViewIfNeeded();
    await c2Section.scrollIntoViewIfNeeded();

    const draggedBox = await draggedCard.boundingBox();
    const targetBox = await c2Section.boundingBox();
    expect(draggedBox).not.toBeNull();
    expect(targetBox).not.toBeNull();

    // `dragTo()` was resolving the drop target as the sortable item itself.
    // Use explicit pointer coordinates to guarantee we end over the target column.
    await page.mouse.move(
      draggedBox!.x + draggedBox!.width / 2,
      draggedBox!.y + draggedBox!.height / 2
    );
    await page.mouse.down();
    await page.mouse.move(
      targetBox!.x + targetBox!.width / 2,
      targetBox!.y + targetBox!.height / 2,
      { steps: 20 }
    );
    await page.mouse.up();

    await expect(c1Section.locator('[data-testid^="card-"]')).toHaveCount(
      c1Before - 1
    );
    await expect(c2Section.getByTestId("card-1")).toBeVisible();
    await expect(c2Section.locator('[data-testid^="card-"]')).toHaveCount(
      c2Before + 1
    );
  });

  test("can reorder a card within a column", async ({ page }) => {
    await page.goto("/");

    const c1Section = page.getByTestId("column-c1");

    const cardIdsBefore = await c1Section
      .locator('[data-testid^="card-"]')
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
    expect(cardIdsBefore).toEqual(["card-1", "card-2"]);

    const draggedCard = page.getByTestId("card-2");
    const targetCard = page.getByTestId("card-1");

    await draggedCard.scrollIntoViewIfNeeded();
    await targetCard.scrollIntoViewIfNeeded();

    const draggedBox = await draggedCard.boundingBox();
    const targetBox = await targetCard.boundingBox();
    expect(draggedBox).not.toBeNull();
    expect(targetBox).not.toBeNull();

    await page.mouse.move(
      draggedBox!.x + draggedBox!.width / 2,
      draggedBox!.y + draggedBox!.height / 2
    );
    await page.mouse.down();
    await page.mouse.move(
      targetBox!.x + targetBox!.width / 2,
      targetBox!.y + targetBox!.height / 2,
      { steps: 20 }
    );
    await page.mouse.up();

    const cardIdsAfter = await c1Section
      .locator('[data-testid^="card-"]')
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));

    expect(cardIdsAfter).toEqual(["card-2", "card-1"]);
  });
});

