# app/(auth)

## 役割

ログインと新規登録の画面を置く。認証前の画面なので、アプリ用の枠は使わず中央寄せの簡素なレイアウトで囲む。ログインはブラウザ側の Supabase クライアントで行い、成功するとトップへ移る（`src/app/(auth)/login/page.tsx`）。

## 主なファイル

- `src/app/(auth)/layout.tsx`（被参照 0）
- `src/app/(auth)/login/page.tsx`（被参照 0）
- `src/app/(auth)/register/page.tsx`（被参照 0）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/app/(auth)/layout.tsx | 1 | function | AuthLayout |
| src/app/(auth)/login/page.tsx | 8 | function | LoginPage |
| src/app/(auth)/register/page.tsx | 8 | function | RegisterPage |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 3 個）。

## 依存先

- `shared/lib`（2 import）

## 依存元

（なし）
