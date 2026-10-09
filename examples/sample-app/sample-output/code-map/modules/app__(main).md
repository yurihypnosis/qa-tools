# app/(main)

## 役割

ログイン後の画面（ダッシュボード、問題集一覧、単語カード、ロードマップ、学習ログ、思考フレーム、コードの読み方など）を置く。サーバーでデータを取り、クライアント側の画面部品へ渡す入口になる。ダッシュボードの本体は `src/app/(main)/learning-app.tsx` にあり、学習ログの日別集計は `src/app/(main)/log/build-days.ts` が担う。

## 主なファイル

- `src/app/(main)/learning-app.tsx`（被参照 2）
- `src/app/(main)/log/build-days.ts`（被参照 2）
- `src/app/(main)/catalog/catalog-client.tsx`（被参照 1）
- `src/app/(main)/code-tour/code-tour-client.tsx`（被参照 1）
- `src/app/(main)/flashcards/flashcards-client.tsx`（被参照 1）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/app/(main)/catalog/catalog-client.tsx | 37 | function | CatalogClient |
| src/app/(main)/code-tour/code-tour-client.tsx | 38 | function | CodeTourClient |
| src/app/(main)/flashcards/flashcards-client.tsx | 13 | function | FlashcardsClient |
| src/app/(main)/learning-app.tsx | 69 | function | LearningApp |
| src/app/(main)/log/build-days.ts | 4 | interface | AnswerEvent |
| src/app/(main)/log/build-days.ts | 13 | interface | DayEntry |
| src/app/(main)/log/build-days.ts | 24 | const | WEEKDAYS |
| src/app/(main)/log/build-days.ts | 30 | function | toDateKey |
| src/app/(main)/log/build-days.ts | 41 | function | shiftKey |
| src/app/(main)/log/build-days.ts | 47 | function | buildDays |
| src/app/(main)/log/build-days.ts | 103 | function | calcStreak |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 29 個）。

## 依存先

- `features/code-tour`（2 import）
- `features/flashcards`（6 import）
- `features/g-kentei-cheatsheet`（2 import）
- `features/mindset`（1 import）
- `features/quiz`（38 import）
- `features/roadmap`（2 import）
- `shared/components`（9 import）
- `shared/lib`（7 import）
- `types`（1 import）

## 依存元

- `features/quiz`（1 import）
