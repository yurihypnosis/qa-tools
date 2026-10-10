# features/mindset

## 役割

勉強の考え方を並べる静的データ。戦略・実行・復習・メンタルの4分類の原則ごとに、その原則の解釈と、学習者の現状に当てはめた行動を持つ。DB は使わない。

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
