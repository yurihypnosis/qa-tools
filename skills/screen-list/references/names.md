# names — 画面名とロールを書く

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `output/screen-list/_raw/pending.jsonl`（1 画面 1 行：`id` `kind` `url` `source` `parents`）、`.qa/screen-list.toml` の `rules.roles` |
| 出力 | 下書き `output/screen-list/_raw/names.draft.jsonl` → `screens.py apply` で取り込む |
| 検査 | `apply` が、キー・画面 ID の存在・名前の長さ（80 字以内）・ロールの語彙を検査する。1 行でも誤りがあれば何も取り込まない |
| 次 | `screens.py merge` を実行する |

## 手順

1. `pending.jsonl` を読む。
2. 各画面の `source`（`ファイル:行`）のファイルを**自分で開いて読み**、名前とロールを書く。画面は、そのファイルから import している同じアプリの部品も読んでよい（見出しや認証の処理が、そこにあることが多い）。
3. 下書きに、1 画面 1 行の JSON を書く。キーは `id` `name` `roles` の 3 つだけ。
   ```json
   {"id": "web/settings", "name": "設定", "roles": ["全員"]}
   ```
4. 次を実行する。
   ```bash
   python3 <skill>/scripts/screens.py apply output/screen-list/_raw/names.draft.jsonl
   ```
   終了コードが 2 なら、メッセージが示す行だけを直して 1 回だけ再実行する。直らなければ、人に報告して止める。

## 画面名

利用者が画面で目にする名前を書く。次の順で探し、最初に見つかったものを使う。

1. **ナビゲーション（サイドバー・ヘッダー・タブ）にある、その画面へのリンクの文言**。画面の URL（`url`）を `href` などに持つ要素を検索する。利用者が画面を呼ぶときの名前に一番近い
2. ページの見出し（`h1` や `title`）
3. 見つからなければ、ファイルの役割から短い名前を付ける

名前は 80 字以内の 1 つの語句にする。

## ロール

その画面を**開ける（見える）ロール**を、`rules.roles` の語彙から選ぶ。誰でも開けるなら `全員`。

- 根拠は、ページやレイアウトの認証・認可の処理（ログイン必須か、ロールの比較があるか）。ソースを読んで確かめられるものだけを書く
- 根拠が見つからないときは、推測せず `["[未解決: 理由]"]` と書く（理由は、何が見つからなかったか）
- `rules.roles` が空なら、書けるのは `全員` か `[未解決: …]` だけ

<examples>
<example>
入力：`{"id": "web/login", "kind": "画面", "url": "/login", "source": "src/screens/login-screen.tsx:1", "parents": []}`（ファイルは認証のガードを持たず、ログインフォームだけを出している）
出力：`{"id": "web/login", "name": "ログイン", "roles": ["全員"]}`
</example>
<example>
入力：`{"id": "web/admin/users", "kind": "画面", "url": "/admin/users", "source": "src/screens/admin-users-screen.tsx:3", "parents": []}`（ファイルが `role !== "admin"` のとき一覧へ戻す）
出力：`{"id": "web/admin/users", "name": "ユーザー管理", "roles": ["管理者"]}`
</example>
<example>
入力：`{"id": "web#src/features/orders/delete-dialog", "kind": "ダイアログ", "url": "", "source": "src/features/orders/delete-dialog.tsx:1", "parents": ["web/orders"]}`（確認の文言と、削除ボタンを持つ。認可の処理は無い）
出力：`{"id": "web#src/features/orders/delete-dialog", "name": "注文の削除の確認", "roles": ["[未解決: ダイアログ自体に認可の処理が無く、開ける画面のロールに従うはず]"]}`
</example>
</examples>
