// ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
// ログイン済みのページを用意する fixture。spec からは tsconfig の paths（@fixtures/auth）で読む。
import { test as base, type Page } from "@playwright/test";

type Fixtures = { adminPage: Page };

export const test = base.extend<Fixtures>({
  adminPage: async ({ page }, use) => {
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill("admin@dummy.example");
    await page.getByLabel("パスワード").fill("dummy-password");
    await page.getByRole("button", { name: "ログイン" }).click();
    await page.waitForURL("/tasks");
    await use(page);
  },
});

export { expect } from "@playwright/test";
