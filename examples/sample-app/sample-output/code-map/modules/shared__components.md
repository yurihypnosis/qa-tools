# shared/components

## 役割

全画面で共通のアプリの枠（サイドバー、トップバー、問題集の切り替え）を置く。画面は見出しや現在の問題集をこの枠へ伝える仕組みを持ち、枠は画面ごとには作り直されない（`src/shared/components/app-shell.tsx`）。

## 主なファイル

- `src/shared/components/app-shell.tsx`（被参照 9）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/shared/components/app-shell.tsx | 32 | function | usePageHeader |
| src/shared/components/app-shell.tsx | 41 | function | useCurrentSubject |
| src/shared/components/app-shell.tsx | 50 | interface | ShellExam |
| src/shared/components/app-shell.tsx | 157 | function | AppShell |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 4 個）。

## 依存先

- `shared/lib`（1 import）

## 依存元

- `app/(main)`（9 import）
