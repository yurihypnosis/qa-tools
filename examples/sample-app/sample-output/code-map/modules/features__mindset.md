# features/mindset

## 役割

勉強の考え方（逆算、回転数、アウトプット重視など）を並べる読み物を置く。公開されている勉強法を下敷きにした思考フレームで、原則ごとに一言の要約、考え方、具体行動を持つ静的データ。データベースは使わず、データは `src/features/mindset/lib/mindset.ts` にある。

## 主なファイル

- `src/features/mindset/lib/mindset.ts`（被参照 1）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/mindset/lib/mindset.ts | 7 | type | MCategory |
| src/features/mindset/lib/mindset.ts | 9 | interface | MPrinciple |
| src/features/mindset/lib/mindset.ts | 21 | const | CATEGORY_META |
| src/features/mindset/lib/mindset.ts | 31 | const | MINDSET_DATA |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 4 個）。

## 依存先

（なし）

## 依存元

- `app/(main)`（1 import）
