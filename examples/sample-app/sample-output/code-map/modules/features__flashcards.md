# features/flashcards

## 役割

単語カード機能を置く。シラバス分野ごとの用語を、やさしい一言・たとえ・正確な定義の三層で持つ静的データと、デッキや分野、範囲による絞り込み、覚えた・苦手の進捗を扱う。データの入口は `src/features/flashcards/lib/flashcards.ts`、絞り込みは `src/features/flashcards/hooks/use-deck-filter.ts` にある。

## 主なファイル

- `src/features/flashcards/lib/flashcards.ts`（被参照 5）
- `src/features/flashcards/hooks/use-deck-filter.ts`（被参照 4）
- `src/features/flashcards/hooks/use-flashcard-session.ts`（被参照 3）
- `src/features/flashcards/lib/constants.ts`（被参照 3）
- `src/features/flashcards/hooks/use-term-progress.ts`（被参照 2）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
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

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 26 個）。

## 依存先

- `features/quiz`（1 import）

## 依存元

- `app/(main)`（6 import）
