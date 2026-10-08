---
name: test-case-generator
description: PBI（プロダクトバックログアイテム）の仕様書・受入基準から、サイジング → テスト分析 → テスト観点（TP / デシジョンテーブル / 確認パターン表）→ 15 列のテストケース → セルフレビューを、QA のレビューゲートで止まりながら段階的に生成する。Use when the user asks to design tests or write test cases from a PBI, spec, ticket, or acceptance criteria — e.g. 「テストケースを作って」「テスト設計して」「観点を出して」「PBI からテスト分析」 — even if they only name a PBI ID such as DUMMY-001. Not for writing automated test code or unit tests.
license: MIT
metadata:
  version: "0.2.0"
---

# Test Case Generator

## Overview

PBI の資料を入力に、5 つの工程で手動テスト用のテストケースを作る。途中に QA のレビューゲートが 2 つあり、AI は QA の合図なしに先へ進まない。成果物はすべて Markdown で `output/{PBI ID}/` に保存する。

この skill は汎用のプロセスだけを持つ。チケット接頭辞・領域コード・ロール名などの製品固有の値は、利用側プロジェクトの `.qa/product.md` から読む。

## When to Use

- PBI・仕様書・受入基準からテスト分析、テスト観点、テストケースを作るとき
- 途中の工程からやり直すとき（`from: viewpoints` など）
- 使わない場面：自動テストのコード、単体テスト、API テスト、性能などの非機能テストの設計

起動例：`/qa-tools:test-case-generator PBI: DUMMY-001 開発サイズ: S from: viewpoints`（PBI 以外は任意）

## 入力の契約

作業ディレクトリ（利用側プロジェクトのルート）に次があることを最初に確かめる。足りなければ、何が足りないかを伝えて止まる。推測で補うと、全工程が誤った前提の上に積み上がるからである。

| 入力 | 必須 | 内容 |
| --- | --- | --- |
| `PBI/{ID}/` | ✅ | 仕様書、受入基準、デザインのメモなど。ID は起動引数の `PBI:` で受け取る |
| `.qa/product.md` | ✅ | チケット接頭辞、領域コード、ロール、出力言語 |
| `.qa/knowledge/` | | 既存機能のナレッジ。画面名・文言の出典として使い、テスト対象にはしない |
| 開発サイズ | | 起動引数の `開発サイズ:`。サイジングで QA 算出サイズと比べる |
| 開始工程 | | 起動引数の `from:`（`sizing` / `analysis` / `viewpoints` / `testcases` / `review`）。既定は `sizing` |

## フロー

```
1 サイジング → 2 テスト分析 → ⛔分析レビュー ─(「観点設計に進んでください」)→ 3 観点設計
  → check_viewpoints → ⛔観点レビュー ─(「ケース生成に進んでください」)→ 4 ケース生成
  → 5 セルフレビュー → 完了報告
```

番号は実行順を示すだけで、工程は名前で呼ぶ。サイジングからテスト分析までと、ケース生成からセルフレビューまでは止まらずに続ける。

各工程では、次の順に進める。

1. **その工程に入ってから**、対応する reference を読む。次の工程の reference は先に読まない。読み込みを工程ごとに区切ることで、コンテキストを今の作業に集中させる。
2. reference の「契約」にある入力を読み、assets の雛形どおりに成果物を Write する。
3. 契約に検査があれば、スクリプトを実行する。
4. 契約の「次」へ進む。

| 工程 | `from:` | reference | 雛形 | 成果物 |
| --- | --- | --- | --- | --- |
| 1 サイジング | `sizing` | [references/1-sizing.md](references/1-sizing.md) | `assets/sizing.template.md` | `1-sizing.md` |
| 2 テスト分析 | `analysis` | [references/2-test-analysis.md](references/2-test-analysis.md) | `assets/analysis.template.md` | `2-analysis.md` |
| 分析レビュー・観点レビュー | — | [references/review-gates.md](references/review-gates.md) | — | — |
| 3 観点設計 | `viewpoints` | [references/3-viewpoint-design.md](references/3-viewpoint-design.md) | `assets/viewpoints.template.md` | `3-viewpoints.md` |
| 4 ケース生成 | `testcases` | [references/4-test-case-generation.md](references/4-test-case-generation.md) | `assets/testcases.template.md` | `4-testcases.md` |
| 5 セルフレビュー | `review` | [references/5-self-review.md](references/5-self-review.md) | `assets/review.template.md` | `5-review.md` |

reference・assets・scripts のパスは、この skill のディレクトリからの相対パスである。成果物のパスは、作業ディレクトリからの相対パスである。

### 再開

- `from: viewpoints` のように指定されたら、その工程から始める。前の工程の成果物が `output/{ID}/` に無ければ、無いことを伝えて止まる。
- 指定が無くても `output/{ID}/` に成果物が既にあるときは、上書きする前に「どの工程から再開するか」を QA に確かめる。QA が直した成果物を黙って上書きしないためである。

### レビューゲート

ゲートの表示項目と自己チェックの手順は `references/review-gates.md` に従う。要点は次のとおり。

- ゲートでは決められた項目だけを表示して、**ターンを終える**。次に進めるのは QA の合図だけである。
- 修正の指示を受けたら、差分 Edit で直し、同じゲートの表示をもう一度出して止まる。
- 観点レビューの前に自己修正してよいのは `BOLD` と `HEADING` だけで、1 回までである。

### 検査スクリプト

標準ライブラリだけで動き、ファイルを書き換えない。`--json` を付けるとレシートを返す。報告は必ずレシートの `status` と `findings` を根拠にする。実行していない検査を「OK」と言わない。

```bash
python3 <skill>/scripts/check_viewpoints.py output/{ID}/3-viewpoints.md --json
python3 <skill>/scripts/check_testcases.py output/{ID}/4-testcases.md --viewpoints output/{ID}/3-viewpoints.md --json
```

終了コードは 0=OK、1=指摘あり、2=入力エラー。`check_testcases.py` は観点ファイルから必要なケース数を数え直し（`TRACE`）、期待結果が太字セルの写しかを確かめる（`EXPECTED`）。ケース生成が自分で書いたトレース表は信用しない。

### 完了報告

セルフレビューの後、次だけを報告して終える。

1. 成果物 5 つのパス
2. QA 算出サイズ（開発サイズと違えば両方）
3. セルフレビュー後の `check_testcases.py` のレシートの結果（ケース数、最終ケース ID、指摘があればその一覧）
4. `5-review.md` の「残った問題」

## Common Rationalizations

| 言い訳 | 実際 |
| --- | --- |
| 「内容に自信があるので、ゲートを飛ばして続けて出す」 | ゲートの目的は、AI が自分では見つけられない読み違いを人が止めることである。自信があるかどうかは関係ない |
| 「開発サイズが書いてあるので、サイジングは省略してよい」 | 開発サイズは実装の工数である。テストの工数は別に見積もらないと、観点やケースの予測がずれる |
| 「`[要確認]` は文脈から推測できるので埋めておく」 | もっともらしい推測は、レビューをすり抜ける誤りの典型である。QA の回答があるまで残す |
| 「期待結果は太字セルを少し言い換えた方が読みやすい」 | 言い換えると、観点とケースの対応を機械的に確かめられなくなる。そのまま写す（`EXPECTED` で落ちる） |
| 「セルフレビューで観点の問題も見つけたので、観点ファイルも直しておく」 | 観点は QA が観点レビューで確定させたものである。直さずに報告する |
| 「検査は形式チェックだけなので、走らせなくても大丈夫」 | 太字漏れ・連番・行数は人の目で見落としやすい。だから機械で見る |

## Red Flags

- QA の合図が無いのに、次の工程の reference を読んだ、またはファイルを書いた
- ゲートで、決められた項目以外（要約・所感・補足）を表示した
- `[要確認]` が理由なく消えている
- 期待結果に、観点ファイルに無い文言がある
- セルフレビューで観点ファイルを書き換えた、または 2 回以上自己修正した
- レシートを見ずに「検査 OK」と報告した
- シェルのリダイレクトで成果物を書いた

## Verification

完了報告の前に確かめる。

- [ ] `output/{ID}/` に `1-sizing.md`〜`5-review.md` の 5 つがある
- [ ] 分析レビュー・観点レビューのそれぞれで、QA の合図を受けてから次へ進んだ
- [ ] `check_viewpoints.py` を観点レビューの前に実行し、レシートを確認した
- [ ] セルフレビューで 2 つの検査を実行し、最後のレシートの内容をそのまま報告した
