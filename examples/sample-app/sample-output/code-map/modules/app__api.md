# app/api

## 役割

問題文を必要な分だけ返す API と、過去の解答履歴から FSRS の復習状態を作り直す一回きりの処理を提供する。どちらもログイン中の本人のデータだけを読み書きする。

## 主なファイル

- `src/app/api/fsrs/backfill/route.ts`（被参照 0）
- `src/app/api/questions/route.ts`（被参照 0）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/app/api/fsrs/backfill/route.ts | 5 | const | dynamic |
| src/app/api/fsrs/backfill/route.ts | 11 | function | POST |
| src/app/api/questions/route.ts | 6 | function | POST |

## 依存先

- `features/quiz`（2 import）
- `shared/lib`（2 import）

## 依存元

（なし）
