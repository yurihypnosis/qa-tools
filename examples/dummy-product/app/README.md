# DUMMY ToDo Cloud のソース（テスト用ダミー）

> ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。

qa-tools のツール（test-steps・code-map・screen-list）に**読ませるためのソース**である。動かすものではないので、`npm install` も `pip install` もしない。

| パス | 中身 | 読むツール |
| --- | --- | --- |
| `src/routes.ts` | 画面のルート定義（6 画面） | screen-list、code-map |
| `src/pages/` | 画面のコンポーネント | screen-list、code-map |
| `src/components/dialogs/` | ダイアログ 2 つ。どちらも `src/components/ui/Dialog.tsx` を使う | screen-list |
| `backend/` | API の Python モジュール 3 つ（auth / tasks / users） | code-map |
| `e2e/` | Playwright の spec 3 本と fixture。fixture は tsconfig の `paths`（`@fixtures/*`）で読む | test-steps |

画面名は `.qa/knowledge/todo-task.md` と同じにしてある（タスク一覧画面、タスク編集ダイアログ）。

## わざと入れたもの

ツールの動作を確かめるために、次の点はわざとそうしてある。直さないこと。

- `e2e/task-delete.spec.ts` は「削除用のタスク」が一覧にある前提だが、そのタスクを作る処理はどこにも無い。test-steps が、書かれていない事前条件を推測で埋めずに `[未解決]` にできるかを確かめるため
