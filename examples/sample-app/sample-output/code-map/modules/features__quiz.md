# features/quiz

## 役割

問題集の演習機能の中心を置く。出題の選び方（休眠、分野、優先度）、採点、習熟度と合格見込みの計算、間隔反復（FSRS）、解答の記録と同期を担い、ダッシュボードや苦手分析、書き出しの画面もここにある。データ型は `src/features/quiz/lib/types.ts`、集計は `src/features/quiz/lib/stats.ts`、出題の選択は `src/features/quiz/lib/selection.ts` にある。

## 主なファイル

- `src/features/quiz/lib/types.ts`（被参照 21）
- `src/features/quiz/lib/stats.ts`（被参照 19）
- `src/features/quiz/lib/selection.ts`（被参照 16）
- `src/features/quiz/hooks/use-screen.ts`（被参照 7）
- `src/features/quiz/hooks/use-supabase-client.ts`（被参照 4）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/quiz/hooks/use-screen.ts | 5 | type | Screen |
| src/features/quiz/hooks/use-screen.ts | 18 | function | useScreen |
| src/features/quiz/hooks/use-supabase-client.ts | 9 | function | useSupabaseClient |
| src/features/quiz/lib/selection.ts | 10 | type | ProgressMap |
| src/features/quiz/lib/selection.ts | 12 | function | getProgress |
| src/features/quiz/lib/selection.ts | 17 | function | totalWrong |
| src/features/quiz/lib/selection.ts | 21 | function | totalCorrect |
| src/features/quiz/lib/selection.ts | 29 | function | isResting |
| src/features/quiz/lib/selection.ts | 51 | function | isEligible |
| src/features/quiz/lib/selection.ts | 55 | function | shuffle |
| src/features/quiz/lib/selection.ts | 72 | function | referencesOptionPositions |
| src/features/quiz/lib/selection.ts | 83 | function | shuffleOptions |
| src/features/quiz/lib/selection.ts | 118 | function | eligibleQuestions |
| src/features/quiz/lib/selection.ts | 132 | interface | BuildDeckArgs |
| src/features/quiz/lib/selection.ts | 144 | function | buildDeck |
| src/features/quiz/lib/stats.ts | 7 | interface | UserGoal |
| src/features/quiz/lib/stats.ts | 13 | interface | Textbook |
| src/features/quiz/lib/stats.ts | 23 | function | masteryFromProgress |
| src/features/quiz/lib/stats.ts | 35 | function | questionMastery |
| src/features/quiz/lib/stats.ts | 45 | function | weakReviewPool |
| src/features/quiz/lib/stats.ts | 69 | interface | MasteryStats |
| src/features/quiz/lib/stats.ts | 80 | function | calcMasteryStats |
| src/features/quiz/lib/stats.ts | 131 | interface | DailyRec |
| src/features/quiz/lib/stats.ts | 139 | function | calcDailyRec |
| src/features/quiz/lib/stats.ts | 171 | interface | CategoryMastery |
| src/features/quiz/lib/stats.ts | 181 | function | calcCategoryMastery |
| src/features/quiz/lib/stats.ts | 238 | function | isSpeakFirstSubject |
| src/features/quiz/lib/stats.ts | 246 | function | examGroupKey |
| src/features/quiz/lib/stats.ts | 251 | function | examDisplayName |
| src/features/quiz/lib/stats.ts | 261 | interface | SectionCatalogItem |
| src/features/quiz/lib/stats.ts | 268 | interface | SectionMastery |
| src/features/quiz/lib/stats.ts | 278 | function | calcSectionMastery |
| src/features/quiz/lib/stats.ts | 327 | interface | QuestionSubjectRef |
| src/features/quiz/lib/stats.ts | 332 | interface | SubjectStat |
| src/features/quiz/lib/stats.ts | 344 | interface | ExamGroup |
| src/features/quiz/lib/stats.ts | 357 | function | buildSubjectStats |
| src/features/quiz/lib/stats.ts | 407 | function | groupSubjectsByExam |
| src/features/quiz/lib/stats.ts | 453 | interface | SectionQuestionRef |
| src/features/quiz/lib/stats.ts | 461 | interface | SetBreakdown |
| src/features/quiz/lib/stats.ts | 468 | interface | SectionAnalysis |
| src/features/quiz/lib/stats.ts | 479 | function | analyzeSections |
| src/features/quiz/lib/stats.ts | 538 | interface | SectionOverview |
| src/features/quiz/lib/stats.ts | 548 | function | sectionOverview |
| src/features/quiz/lib/types.ts | 2 | const | FLAGS |
| src/features/quiz/lib/types.ts | 3 | const | FLAG_COLORS |
| src/features/quiz/lib/types.ts | 5 | const | WEEK_MS |
| src/features/quiz/lib/types.ts | 6 | const | TWO_WEEKS_MS |
| src/features/quiz/lib/types.ts | 8 | type | QuizMode |
| src/features/quiz/lib/types.ts | 11 | interface | ExplanationData |
| src/features/quiz/lib/types.ts | 34 | interface | QuizQuestion |
| src/features/quiz/lib/types.ts | 55 | interface | Progress |
| src/features/quiz/lib/types.ts | 80 | function | emptyProgress |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 134 個）。

## 依存先

- `app/(main)`（1 import）
- `shared/lib`（1 import）
- `types`（1 import）

## 依存元

- `app/(main)`（38 import）
- `app/api`（2 import）
- `features/flashcards`（1 import）
