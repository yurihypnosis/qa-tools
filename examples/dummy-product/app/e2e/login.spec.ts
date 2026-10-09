// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
import { expect, test } from "@playwright/test";

test.describe("ログイン", () => {
  test("正しいメールアドレスとパスワードでタスク一覧画面に移る", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill("admin@dummy.example");
    await page.getByLabel("パスワード").fill("dummy-password");
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page).toHaveURL("/tasks");
    await expect(page.getByRole("heading", { name: "タスク一覧" })).toBeVisible();
  });

  test("パスワードが違うとエラーを表示する", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill("admin@dummy.example");
    await page.getByLabel("パスワード").fill("wrong-password");
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page.getByRole("alert")).toHaveText("メールアドレスかパスワードが違います");
    await expect(page).toHaveURL("/login");
  });
});
