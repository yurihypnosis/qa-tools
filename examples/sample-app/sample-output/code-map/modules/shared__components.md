# shared/components

## 役割

アプリ全体の枠組み。サイドバーとトップバーのシェルを持ち、配下のページがトップバーの見出しと現在の問題集を設定できる。ページ遷移をまたいで状態を保つ。

## 主なファイル

- `src/shared/components/app-shell.tsx`（被参照 9）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/shared/components/app-shell.tsx | 32 | function | usePageHeader |
| src/shared/components/app-shell.tsx | 41 | function | useCurrentSubject |
| src/shared/components/app-shell.tsx | 50 | interface | ShellExam |
| src/shared/components/app-shell.tsx | 157 | function | AppShell |

## 依存先

- `shared/lib`（1 import）

## 依存元

- `app/(main)`（9 import）
