# アーキテクチャ

## モジュール間の依存

| 依存元 | 依存先 | import 数 |
| --- | --- | --- |
| (root) | shared/lib | 1 |
| app/(auth) | shared/lib | 2 |
| app/(main) | features/code-tour | 2 |
| app/(main) | features/flashcards | 6 |
| app/(main) | features/g-kentei-cheatsheet | 2 |
| app/(main) | features/mindset | 1 |
| app/(main) | features/quiz | 38 |
| app/(main) | features/roadmap | 2 |
| app/(main) | shared/components | 9 |
| app/(main) | shared/lib | 7 |
| app/(main) | types | 1 |
| app/api | features/quiz | 2 |
| app/api | shared/lib | 2 |
| features/flashcards | features/quiz | 1 |
| features/quiz | app/(main) | 1 |
| features/quiz | shared/lib | 1 |
| features/quiz | types | 1 |
| shared/components | shared/lib | 1 |
| shared/lib | types | 3 |
