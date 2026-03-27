import { expect, test, type Page } from "@playwright/test";

const login = async (page: Page) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /login/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("logs in and logs out", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
});

test("rejects invalid credentials", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /login/i }).click();
  await expect(page.getByText(/invalid username\/password/i)).toBeVisible();
});

test("adds a card and keeps it after reload", async ({ page }) => {
  await login(page);

  const firstColumn = page.getByTestId("column-col-backlog");
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();

  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
  await expect(page.getByText("All changes saved")).toBeVisible();

  await page.reload();
  await expect(page.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns and keeps it after reload", async ({ page }) => {
  await login(page);

  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();

  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
  await expect(page.getByText("All changes saved")).toBeVisible();

  await page.reload();
  await expect(page.getByTestId("column-col-review").getByTestId("card-card-1")).toBeVisible();
});
