# features/g-kentei-cheatsheet

## 役割

G検定チートシートの用語データの型と、用語を一覧して関連する用語どうしを比べて見せる画面。用語の関連は問題ごとの比較文から作り、新しい比較文は作らない。

## 主なファイル

- `src/features/g-kentei-cheatsheet/lib/types.ts`（被参照 2）
- `src/features/g-kentei-cheatsheet/screens/cheatsheet-screen.tsx`（被参照 1）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/g-kentei-cheatsheet/lib/types.ts | 1 | interface | TermExample |
| src/features/g-kentei-cheatsheet/lib/types.ts | 7 | interface | TermEntry |
| src/features/g-kentei-cheatsheet/lib/types.ts | 18 | interface | ComparisonGroup |
| src/features/g-kentei-cheatsheet/screens/cheatsheet-screen.tsx | 172 | function | CheatsheetScreen |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 4 個）。

## 依存先

（なし）

## 依存元

- `app/(main)`（2 import）
