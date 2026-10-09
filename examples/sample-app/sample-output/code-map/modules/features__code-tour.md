# features/code-tour

## 役割

「コードの読み方」ガイドの内容を置く。このリポジトリ自体を教材に、初見のコードを読む型を身につけるための静的な読み物で、データベースは使わない。トピックと練習課題のデータは `src/features/code-tour/lib/code-tour.ts` にある。

## 主なファイル

- `src/features/code-tour/components/diagrams.tsx`（被参照 1）
- `src/features/code-tour/lib/code-tour.ts`（被参照 1）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/code-tour/components/diagrams.tsx | 55 | function | DiagramHierarchy |
| src/features/code-tour/components/diagrams.tsx | 82 | function | DiagramFolders |
| src/features/code-tour/components/diagrams.tsx | 153 | function | DiagramServerClient |
| src/features/code-tour/components/diagrams.tsx | 211 | function | DiagramDataFlow |
| src/features/code-tour/components/diagrams.tsx | 245 | function | DiagramFeatureAnatomy |
| src/features/code-tour/components/diagrams.tsx | 278 | function | DiagramSupabaseClients |
| src/features/code-tour/components/diagrams.tsx | 323 | function | DiagramTestAsSpec |
| src/features/code-tour/components/diagrams.tsx | 356 | function | DiagramUnknownCodeFlow |
| src/features/code-tour/lib/code-tour.ts | 5 | type | CtSection |
| src/features/code-tour/lib/code-tour.ts | 7 | const | SECTION_META |
| src/features/code-tour/lib/code-tour.ts | 14 | interface | CtExercise |
| src/features/code-tour/lib/code-tour.ts | 24 | const | CODE_TOUR_EXERCISES |
| src/features/code-tour/lib/code-tour.ts | 72 | interface | CtTopic |
| src/features/code-tour/lib/code-tour.ts | 84 | const | CODE_TOUR_DATA |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 14 個）。

## 依存先

（なし）

## 依存元

- `app/(main)`（2 import）
