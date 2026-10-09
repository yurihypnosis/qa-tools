# features/flashcards

## 役割

単語カード機能。G検定向けの用語データと、分野や範囲による出題の絞り込み、セッションの進行を担う。用語ごとの定着状態は DB に保存し、設定・出題・結果の3画面を組み立てる。

## 主なファイル

- `src/features/flashcards/lib/flashcards.ts`（被参照 5）
- `src/features/flashcards/hooks/use-deck-filter.ts`（被参照 4）
- `src/features/flashcards/hooks/use-flashcard-session.ts`（被参照 3）
- `src/features/flashcards/lib/constants.ts`（被参照 3）
- `src/features/flashcards/hooks/use-term-progress.ts`（被参照 2）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/flashcards/components/filter-chip.tsx | 1 | function | FilterChip |
| src/features/flashcards/hooks/use-deck-filter.ts | 7 | type | Scope |
| src/features/flashcards/hooks/use-deck-filter.ts | 14 | function | useDeckFilter |
| src/features/flashcards/hooks/use-flashcard-session.ts | 16 | type | Phase |
| src/features/flashcards/hooks/use-flashcard-session.ts | 95 | function | useFlashcardSession |
| src/features/flashcards/hooks/use-term-progress.ts | 10 | type | TermRow |
| src/features/flashcards/hooks/use-term-progress.ts | 17 | type | TermStat |
| src/features/flashcards/hooks/use-term-progress.ts | 18 | type | DeckProgress |
| src/features/flashcards/hooks/use-term-progress.ts | 19 | type | Store |
| src/features/flashcards/hooks/use-term-progress.ts | 20 | type | Status |
| src/features/flashcards/hooks/use-term-progress.ts | 28 | function | useTermProgress |
| src/features/flashcards/lib/constants.ts | 1 | const | MASTERED |
| src/features/flashcards/lib/constants.ts | 2 | const | WEAK |
| src/features/flashcards/lib/constants.ts | 4 | const | wrap |
| src/features/flashcards/lib/constants.ts | 5 | const | container |
| src/features/flashcards/lib/constants.ts | 6 | const | lbl |
| src/features/flashcards/lib/flashcards.ts | 7 | interface | FlashCard |
| src/features/flashcards/lib/flashcards.ts | 17 | interface | FlashDeck |
| src/features/flashcards/lib/flashcards.ts | 24 | const | FLASHCARD_CATEGORY_ORDER |
| src/features/flashcards/lib/flashcards.ts | 27 | const | FLASHCARD_CATEGORY_COLOR |
| src/features/flashcards/lib/flashcards.ts | 38 | function | categoryColor |
| src/features/flashcards/lib/flashcards.ts | 346 | const | FLASHCARD_DECKS |
| src/features/flashcards/lib/flashcards.ts | 352 | function | deckByKey |
| src/features/flashcards/screens/done-screen.tsx | 10 | function | DoneScreen |
| src/features/flashcards/screens/session-screen.tsx | 11 | function | SessionScreen |
| src/features/flashcards/screens/setup-screen.tsx | 16 | function | SetupScreen |

## 依存先

- `features/quiz`（1 import）

## 依存元

- `app/(main)`（6 import）
