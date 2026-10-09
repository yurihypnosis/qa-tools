# features/roadmap

## 役割

学習ロードマップのデータモデルと既定値。フェーズと項目の型、既定のロードマップを持つ。保存された内容がなければ既定値を使い、サーバとクライアントの両方で使われる。

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

## 依存先

（なし）

## 依存元

- `app/(main)`（2 import）
