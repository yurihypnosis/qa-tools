// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
import { expect, test } from "@fixtures/auth";

test("確認ダイアログで「削除する」を押すと、一覧からタスクが消える", async ({ adminPage: page }) => {
  await page.goto("/tasks");
  const row = page.getByRole("listitem").filter({ hasText: "削除用のタスク" });
  await row.getByRole("button", { name: "削除" }).click();
  const dialog = page.getByRole("dialog", { name: "タスクを削除しますか？" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "削除する" }).click();
  await expect(row).toHaveCount(0);
});

test("確認ダイアログで「キャンセル」を押すと、タスクは残る", async ({ adminPage: page }) => {
  await page.goto("/tasks");
  const row = page.getByRole("listitem").filter({ hasText: "削除用のタスク" });
  await row.getByRole("button", { name: "削除" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "キャンセル" }).click();
  await expect(row).toHaveCount(1);
});
