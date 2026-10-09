# app/(main)

## 役割

ログイン後の主要画面群。ダッシュボード、問題集一覧、単語カード、コードの読み方、ロードマップ、学習ログ、考え方の各ページを持つ。features 配下の画面部品とフックを組み合わせて各ページを作り、学習ログ用の日別集計もここで扱う。

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
| src/app/(main)/catalog/page.tsx | 6 | const | dynamic |
| src/app/(main)/catalog/page.tsx | 8 | function | CatalogPage |
| src/app/(main)/code-tour/code-tour-client.tsx | 38 | function | CodeTourClient |
| src/app/(main)/code-tour/page.tsx | 3 | function | CodeTourPage |
| src/app/(main)/flashcards/flashcards-client.tsx | 13 | function | FlashcardsClient |
| src/app/(main)/flashcards/page.tsx | 4 | const | dynamic |
| src/app/(main)/flashcards/page.tsx | 6 | function | FlashcardsPage |
| src/app/(main)/g-kentei/cheatsheet/page.tsx | 6 | function | GKenteiCheatsheetPage |
| src/app/(main)/layout.tsx | 9 | function | MainLayout |
| src/app/(main)/learning-app.tsx | 69 | function | LearningApp |
| src/app/(main)/log/build-days.ts | 4 | interface | AnswerEvent |
| src/app/(main)/log/build-days.ts | 13 | interface | DayEntry |
| src/app/(main)/log/build-days.ts | 24 | const | WEEKDAYS |
| src/app/(main)/log/build-days.ts | 30 | function | toDateKey |
| src/app/(main)/log/build-days.ts | 41 | function | shiftKey |
| src/app/(main)/log/build-days.ts | 47 | function | buildDays |
| src/app/(main)/log/build-days.ts | 103 | function | calcStreak |
| src/app/(main)/log/log-client.tsx | 107 | function | LogClient |
| src/app/(main)/log/page.tsx | 6 | const | dynamic |
| src/app/(main)/log/page.tsx | 15 | function | LogPage |
| src/app/(main)/mindset/mindset-client.tsx | 22 | function | MindsetClient |
| src/app/(main)/mindset/page.tsx | 3 | function | MindsetPage |
| src/app/(main)/overview-dashboard.tsx | 27 | function | OverviewDashboard |
| src/app/(main)/page.tsx | 16 | const | dynamic |
| src/app/(main)/page.tsx | 81 | function | HomePage |
| src/app/(main)/roadmap/page.tsx | 12 | const | dynamic |
| src/app/(main)/roadmap/page.tsx | 14 | function | RoadmapPage |
| src/app/(main)/roadmap/roadmap-client.tsx | 55 | function | RoadmapClient |

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
