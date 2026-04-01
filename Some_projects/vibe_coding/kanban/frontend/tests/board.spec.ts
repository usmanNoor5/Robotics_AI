import { expect, test } from "@playwright/test";

test("supports rename, add, delete, and drag-and-drop flows", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Aurora Sprint Board" }),
  ).toBeVisible();
  await expect(page.getByTestId("column-strategy")).toBeVisible();
  await expect(page.getByTestId("column-ready-to-launch")).toBeVisible();

  const renameInput = page.locator("#column-name-strategy");
  await renameInput.fill("Concept Lab");
  await renameInput.blur();
  await expect(renameInput).toHaveValue("Concept Lab");

  const strategyColumn = page.getByTestId("column-strategy");
  const strategySection = renameInput.locator("xpath=ancestor::section[1]");

  await strategySection.getByRole("button", { name: "Add Card" }).click();
  await page.getByLabel("Card Title").fill("Polish operator checklist");
  await page
    .getByLabel("Card Details")
    .fill("Capture the exact pre-demo checks so the room setup stays calm.");
  await page.getByRole("button", { name: "Create Card" }).click();
  await expect(strategyColumn.getByText("Polish operator checklist")).toBeVisible();

  await strategyColumn
    .locator('button[aria-label="Delete Polish operator checklist"]')
    .click();
  await expect(strategyColumn.getByText("Polish operator checklist")).toHaveCount(0);

  const draggableCard = page.getByTestId("card-card-roadmap");
  await draggableCard.focus();
  await page.keyboard.press("Space");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Space");

  await expect(page.getByTestId("column-in-motion").getByText("Finalize Q2 roadmap")).toBeVisible();
  await expect(page.getByTestId("column-strategy").getByText("Finalize Q2 roadmap")).toHaveCount(0);
});
