# (root)

## 役割

Next.js のすべてのリクエストの前に動く前処理（proxy）を置く。Supabase の認証セッションを更新し、未ログインなら /login へ、ログイン済みで認証画面を開いたら / へ振り分ける。

## 主なファイル

- `src/proxy.ts`（被参照 0）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/proxy.ts | 4 | function | proxy |
| src/proxy.ts | 8 | const | config |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 2 個）。

## 依存先

- `shared/lib`（1 import）

## 依存元

（なし）
