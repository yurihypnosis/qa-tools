# types

## 役割

データベースの表と関数の型定義を一か所に集めて置く。各モジュールはここから行の形を借りて、型を付けてデータを読み書きする（`src/types/database.ts`）。

## 主なファイル

- `src/types/database.ts`（被参照 5）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/types/database.ts | 1 | type | Json |
| src/types/database.ts | 9 | interface | Database |
| src/types/database.ts | 376 | type | Tables |
| src/types/database.ts | 378 | type | InsertTables |
| src/types/database.ts | 380 | type | UpdateTables |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 5 個）。

## 依存先

（なし）

## 依存元

- `app/(main)`（1 import）
- `features/quiz`（1 import）
- `shared/lib`（3 import）
