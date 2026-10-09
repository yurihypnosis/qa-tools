# features/roadmap

## 役割

学習ロードマップ（フェーズと項目）のデータモデルと既定の内容を置く。項目の完了状態は利用者ごとにデータベースへ保存され、この定義と組み合わせて表示される。既定の内容と型は `src/features/roadmap/lib/roadmap.ts` にある。

## 主なファイル

- `src/features/roadmap/lib/roadmap.ts`（被参照 2）

## 公開シンボル

| ファイル | 行 | 種類 | 名前 |
| --- | --- | --- | --- |
| src/features/roadmap/lib/roadmap.ts | 5 | type | RStatus |
| src/features/roadmap/lib/roadmap.ts | 6 | type | RItemKind |
| src/features/roadmap/lib/roadmap.ts | 8 | interface | RItem |
| src/features/roadmap/lib/roadmap.ts | 17 | interface | RPhase |
| src/features/roadmap/lib/roadmap.ts | 27 | interface | RoadmapDoc |
| src/features/roadmap/lib/roadmap.ts | 33 | const | DEFAULT_ROADMAP |
| src/features/roadmap/lib/roadmap.ts | 70 | function | cloneDoc |
| src/features/roadmap/lib/roadmap.ts | 75 | function | defaultDocWithLegacyDone |
| src/features/roadmap/lib/roadmap.ts | 86 | function | isRoadmapDoc |
| src/features/roadmap/lib/roadmap.ts | 93 | function | newId |

代表ファイルのシンボルだけを示す。全部は `lookup/symbol_index.tsv`（このモジュールは 10 個）。

## 依存先

（なし）

## 依存元

- `app/(main)`（2 import）
