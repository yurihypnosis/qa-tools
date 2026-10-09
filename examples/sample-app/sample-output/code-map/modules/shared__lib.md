# shared/lib

## 役割

Supabase への接続の窓口（ブラウザ用、サーバー用、ミドルウェア用）と、小さな共通関数を置く。Supabase の窓口はどれもログイン中の利用者を前提にして、本人のデータへ絞って読み書きする（`src/shared/lib/supabase/server.ts`）。

## 主なファイル

- `src/shared/lib/supabase/server.ts`（被参照 8）
- `src/shared/lib/supabase/client.ts`（被参照 5）
- `src/shared/lib/supabase/middleware.ts`（被参照 1）
- `src/shared/lib/utils.ts`（被参照 0）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/shared/lib/supabase/client.ts | 4 | function | createClient |
| src/shared/lib/supabase/middleware.ts | 5 | function | updateSession |
| src/shared/lib/supabase/server.ts | 6 | function | createServerSupabaseClient |
| src/shared/lib/supabase/server.ts | 33 | const | getServerSupabase |
| src/shared/lib/supabase/server.ts | 46 | const | getSessionUser |
| src/shared/lib/utils.ts | 4 | function | cn |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 6 個）。

## 依存先

- `types`（3 import）

## 依存元

- `(root)`（1 import）
- `app/(auth)`（2 import）
- `app/(main)`（7 import）
- `app/api`（2 import）
- `features/quiz`（1 import）
- `shared/components`（1 import）
