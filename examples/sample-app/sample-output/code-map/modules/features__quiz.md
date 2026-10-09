# features/quiz

## 役割

問題演習の中核。問題・解説・進捗の型、FSRS による間隔反復、正誤判定、出題の選び方、習得度や合格見込みの統計を計算する。演習・分析・目標・CSV 出力の各画面とそのためのフックを持ち、ダッシュボードや単語カードからも型と統計を使われる。

## 主なファイル

- `src/features/quiz/lib/types.ts`（被参照 21）
- `src/features/quiz/lib/stats.ts`（被参照 19）
- `src/features/quiz/lib/selection.ts`（被参照 16）
- `src/features/quiz/hooks/use-screen.ts`（被参照 7）
- `src/features/quiz/hooks/use-supabase-client.ts`（被参照 4）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/quiz/components/dashboard-parts.tsx | 6 | interface | WeeklyBar |
| src/features/quiz/components/dashboard-parts.tsx | 12 | function | Ico |
| src/features/quiz/components/dashboard-parts.tsx | 29 | function | StatCard |
| src/features/quiz/components/dashboard-parts.tsx | 65 | interface | Totals |
| src/features/quiz/components/dashboard-parts.tsx | 73 | function | StatGrid |
| src/features/quiz/components/dashboard-parts.tsx | 152 | function | ActivityCard |
| src/features/quiz/components/dashboard-parts.tsx | 220 | function | ProgressTable |
| src/features/quiz/components/rich-explanation.tsx | 66 | function | RichExplanation |
| src/features/quiz/components/theme-practice.tsx | 23 | function | ThemePractice |
| src/features/quiz/components/trend-card.tsx | 5 | interface | TrendDay |
| src/features/quiz/components/trend-card.tsx | 120 | function | TrendCard |
| src/features/quiz/hooks/use-csv-export.ts | 17 | function | useCsvExport |
| src/features/quiz/hooks/use-exam-goal.ts | 15 | function | useExamGoal |
| src/features/quiz/hooks/use-fsrs-backfill.ts | 7 | function | useFsrsBackfill |
| src/features/quiz/hooks/use-menu-settings.ts | 22 | function | useMenuSettings |
| src/features/quiz/hooks/use-now.ts | 7 | function | useNow |
| src/features/quiz/hooks/use-progress.ts | 17 | function | useProgress |
| src/features/quiz/hooks/use-progress.ts | 100 | type | PersistFn |
| src/features/quiz/hooks/use-progress.ts | 101 | type | RecordAnswerFn |
| src/features/quiz/hooks/use-quiz-session.ts | 11 | type | SessionResult |
| src/features/quiz/hooks/use-quiz-session.ts | 87 | function | sessionReducer |
| src/features/quiz/hooks/use-quiz-session.ts | 156 | function | useQuizSession |
| src/features/quiz/hooks/use-readiness.ts | 35 | function | useReadiness |
| src/features/quiz/hooks/use-screen.ts | 5 | type | Screen |
| src/features/quiz/hooks/use-screen.ts | 18 | function | useScreen |
| src/features/quiz/hooks/use-supabase-client.ts | 9 | function | useSupabaseClient |
| src/features/quiz/hooks/use-textbooks.ts | 15 | function | useTextbooks |
| src/features/quiz/lib/constants.ts | 5 | const | WEAK_SESSION_MAX |
| src/features/quiz/lib/constants.ts | 7 | const | VERDICT_META |
| src/features/quiz/lib/constants.ts | 15 | const | CONFIDENCE_LABELS |
| src/features/quiz/lib/constants.ts | 19 | const | CONFIDENCE_COLORS |
| src/features/quiz/lib/constants.ts | 24 | const | COMPREHENSION_LEVELS |
| src/features/quiz/lib/csv.ts | 6 | type | ExportMode |
| src/features/quiz/lib/csv.ts | 21 | function | buildCSV |
| src/features/quiz/lib/csv.ts | 62 | function | downloadCSV |
| src/features/quiz/lib/format.ts | 2 | function | fmtLastStudied |
| src/features/quiz/lib/format.ts | 16 | function | accuracyColor |
| src/features/quiz/lib/format.ts | 24 | function | statusOf |
| src/features/quiz/lib/fsrs.ts | 11 | type | Grade |
| src/features/quiz/lib/fsrs.ts | 13 | interface | Card |
| src/features/quiz/lib/fsrs.ts | 23 | interface | FsrsParams |
| src/features/quiz/lib/fsrs.ts | 30 | const | DEFAULT_WEIGHTS |
| src/features/quiz/lib/fsrs.ts | 35 | const | DEFAULT_PARAMS |
| src/features/quiz/lib/fsrs.ts | 49 | function | retrievability |
| src/features/quiz/lib/fsrs.ts | 55 | function | intervalFromStability |
| src/features/quiz/lib/fsrs.ts | 97 | function | gradeFromAnswer |
| src/features/quiz/lib/fsrs.ts | 104 | function | newCard |
| src/features/quiz/lib/fsrs.ts | 117 | function | review |
| src/features/quiz/lib/fsrs.ts | 157 | function | isDue |
| src/features/quiz/lib/fsrs.ts | 163 | function | currentRetrievability |
| src/features/quiz/lib/grading.ts | 5 | function | arraysEqual |
| src/features/quiz/lib/grading.ts | 10 | function | cardFromProgress |
| src/features/quiz/lib/grading.ts | 23 | function | fsrsFields |
| src/features/quiz/lib/readiness.ts | 13 | const | EXAM_PASS_LINE |
| src/features/quiz/lib/readiness.ts | 22 | function | passLineFor |
| src/features/quiz/lib/readiness.ts | 28 | function | capacityFromDailyCounts |
| src/features/quiz/lib/readiness.ts | 36 | function | retentionEstimate |
| src/features/quiz/lib/readiness.ts | 58 | function | itemCorrectProb |
| src/features/quiz/lib/readiness.ts | 66 | function | poissonBinomialPMF |
| src/features/quiz/lib/readiness.ts | 81 | function | passProbability |
| src/features/quiz/lib/readiness.ts | 93 | function | demonstratedSkill |
| src/features/quiz/lib/readiness.ts | 107 | function | examItemProb |
| src/features/quiz/lib/readiness.ts | 129 | interface | ExamItem |
| src/features/quiz/lib/readiness.ts | 139 | function | estimatePassProbability |
| src/features/quiz/lib/readiness.ts | 165 | type | Verdict |
| src/features/quiz/lib/readiness.ts | 167 | interface | Readiness |
| src/features/quiz/lib/readiness.ts | 181 | interface | ReadinessInput |
| src/features/quiz/lib/readiness.ts | 191 | function | computeReadiness |
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
| src/features/quiz/lib/server-data.ts | 15 | function | fetchAllRows |
| src/features/quiz/lib/server-data.ts | 35 | interface | SubjectStatsRow |
| src/features/quiz/lib/server-data.ts | 48 | function | fetchSubjectStats |
| src/features/quiz/lib/server-data.ts | 125 | function | toSubjectStats |
| src/features/quiz/lib/server-data.ts | 146 | interface | DayCount |
| src/features/quiz/lib/server-data.ts | 158 | function | fetchDailyCounts |
| src/features/quiz/lib/server-data.ts | 200 | function | jstDayKey |
| src/features/quiz/lib/server-data.ts | 205 | function | fetchFamilyProgress |
| src/features/quiz/lib/server-data.ts | 265 | interface | TrendDay |
| src/features/quiz/lib/server-data.ts | 279 | function | fetchDailyBreakdown |
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
| src/features/quiz/lib/streak.ts | 1 | function | countStreak |
| src/features/quiz/lib/types.ts | 2 | const | FLAGS |
| src/features/quiz/lib/types.ts | 3 | const | FLAG_COLORS |
| src/features/quiz/lib/types.ts | 5 | const | WEEK_MS |
| src/features/quiz/lib/types.ts | 6 | const | TWO_WEEKS_MS |
| src/features/quiz/lib/types.ts | 8 | type | QuizMode |
| src/features/quiz/lib/types.ts | 11 | interface | ExplanationData |
| src/features/quiz/lib/types.ts | 34 | interface | QuizQuestion |
| src/features/quiz/lib/types.ts | 55 | interface | Progress |
| src/features/quiz/lib/types.ts | 80 | function | emptyProgress |
| src/features/quiz/screens/analysis-screen.tsx | 45 | function | AnalysisScreen |
| src/features/quiz/screens/done-screen.tsx | 16 | function | DoneScreen |
| src/features/quiz/screens/export-screen.tsx | 15 | function | ExportScreen |
| src/features/quiz/screens/goal-screen.tsx | 14 | function | GoalScreen |
| src/features/quiz/screens/menu-screen.tsx | 65 | function | MenuScreen |
| src/features/quiz/screens/quiz-screen.tsx | 20 | function | QuizScreen |

## 依存先

- `app/(main)`（1 import）
- `shared/lib`（1 import）
- `types`（1 import）

## 依存元

- `app/(main)`（38 import）
- `app/api`（2 import）
- `features/flashcards`（1 import）
