# app/api

## 役割

ブラウザから呼ばれる API ルートを置く。問題を選択肢や解説込みで取り直す `questions` と、過去の解答履歴から FSRS の記憶状態を再計算する `src/app/api/fsrs/backfill/route.ts` の二つがある。どちらも本人のセッションを確認してから、本人の行だけを読み書きする。

## 主なファイル

- `src/app/api/fsrs/backfill/route.ts`（被参照 0）
- `src/app/api/questions/route.ts`（被参照 0）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/app/api/fsrs/backfill/route.ts | 5 | const | dynamic |
| src/app/api/fsrs/backfill/route.ts | 11 | function | POST |
| src/app/api/questions/route.ts | 6 | function | POST |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 3 個）。

## 依存先

- `features/quiz`（2 import）
- `shared/lib`（2 import）

## 依存元

（なし）
