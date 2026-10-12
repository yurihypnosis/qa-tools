# roles — モジュールの役割を書く

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `output/code-map/_raw/pending.jsonl`（1 モジュール 1 行：`module` `files` `representatives`） |
| 出力 | 下書き `output/code-map/_raw/roles.draft.jsonl` → `codemap.py apply` で取り込む |
| 検査 | `apply` が、キー・モジュールの存在・長さ（600 字以内）を検査する。1 行でも誤りがあれば何も取り込まない |
| 次 | `codemap.py assemble` を実行する |

## 手順

1. `pending.jsonl` を読む。
2. 各モジュールについて、`representatives`（被参照数の多い順の代表ファイル）を**自分で開いて読み**、役割を書く。ファイルを読まずに、モジュール名から推測しない。
3. 下書きに、1 モジュール 1 行の JSON を書く。キーは `module` と `role` だけ。
   ```json
   {"module": "features/billing", "role": "請求の作成と集計を担う。…"}
   ```
4. 次を実行する。
   ```bash
   python3 <skill>/scripts/codemap.py apply output/code-map/_raw/roles.draft.jsonl
   ```
   終了コードが 2 なら、メッセージが示す行だけを直して 1 回だけ再実行する。直らなければ、人に報告して止める。

## 役割の書き方

- 2〜4 文。このモジュールが**何のためにあるか**と、**他のモジュールから見て何を提供するか**を書く。
- ファイルや関数の一覧は書かない（スクリプトが `主なファイル` と `公開シンボル` に出す）。
- 入口のファイルを示したいときだけ、`tree.md` にあるパスをバッククォートで囲んで書く。
- コードに書かれていないこと（目的の推測、将来の予定）を書かない。分からない部分は、書かずに省く。

<examples>
<example>
入力：`{"module": "features/billing", "representatives": [{"path": "src/features/billing/lib/types.ts", "imported_by": 14}, {"path": "src/features/billing/lib/totals.ts", "imported_by": 5}]}`
出力：`{"module": "features/billing", "role": "請求の作成と集計を担う。金額の計算（`src/features/billing/lib/totals.ts`）と請求データの型を持ち、画面側からはフックと画面部品を通して使われる。"}`
</example>
<example>
入力：`{"module": "shared/lib", "representatives": [{"path": "src/shared/lib/utils.ts", "imported_by": 20}]}`
出力：`{"module": "shared/lib", "role": "アプリ全体で使う小さな共通処理を置く。クラス名の結合など、機能に属さない関数が中心。"}`
</example>
<example>
入力：`{"module": "(root)", "representatives": [{"path": "src/proxy.ts", "imported_by": 0}]}`
出力：`{"module": "(root)", "role": "ルート直下の設定的なファイル。リクエストを受けたときの前処理（`src/proxy.ts`）を持つ。"}`
</example>
</examples>
