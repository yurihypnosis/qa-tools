// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
import { expect, test } from "@fixtures/auth";

test("タスク名を入力して作成すると、詳細画面に移る", async ({ adminPage: page }) => {
  await page.goto("/tasks/new");
  await page.getByLabel("タスク名").fill("週次レポートを書く");
  await page.getByRole("button", { name: "作成" }).click();
  await expect(page).toHaveURL(/\/tasks\/\d+$/);
  await expect(page.getByRole("heading", { name: "週次レポートを書く" })).toBeVisible();
});

test("タスク名が空だと作成できない", async ({ adminPage: page }) => {
  await page.goto("/tasks/new");
  await page.getByRole("button", { name: "作成" }).click();
  await expect(page.getByRole("alert")).toHaveText("タスク名を入力してください");
  await expect(page).toHaveURL("/tasks/new");
});
