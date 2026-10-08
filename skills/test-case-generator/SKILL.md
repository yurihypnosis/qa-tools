---
name: test-case-generator
description: PBI（プロダクトバックログアイテム）の仕様書・受入基準から、テスト分析 → テスト観点（TP / デシジョンテーブル / 確認パターン表）→ 15 列のテストケースを、QA のレビューゲートで止まりながら段階的に生成する。Use when the user asks to design tests or write test cases from a PBI, spec, ticket, or acceptance criteria — e.g. 「テストケースを作って」「テスト設計して」「観点を出して」「/test-design」「PBI からテスト分析」 — even if they only name a PBI ID such as DUMMY-001. Not for writing automated test code or unit tests.
license: MIT
metadata:
  version: "0.1.0"
---

# Test Case Generator

## Overview

PBI の資料を入力に、3 つの Step で手動テスト用のテストケースを作る。Step の間には QA のレビューゲートがあり、AI は QA の合図なしに次の Step へ進まない。成果物はすべて Markdown で `output/{PBI ID}/` に保存する。

この skill は汎用のプロセスだけを持つ。チケット接頭辞・領域コード・ロール名などの製品固有の値は、利用側プロジェクトの `.qa/product.md` から読む。

## When to Use

- PBI・仕様書・受入基準からテスト分析、テスト観点、テストケースを作るとき
- 途中の Step からやり直すとき（`from: step2` など）
- 使わない場面：自動テストのコード、単体テスト、API テスト、性能などの非機能テストの設計

## 入力の契約

作業ディレクトリ（利用側プロジェクトのルート）に次があることを最初に確かめる。足りなければ、何が足りないかを伝えて止まる。推測で補うと、全 Step が誤った前提の上に積み上がるからである。

| 入力 | 必須 | 内容 |
| --- | --- | --- |
| `PBI/{ID}/` | ✅ | 仕様書、受入基準、デザインのメモなど。ID は起動引数の `PBI:` で受け取る |
| `.qa/product.md` | ✅ | チケット接頭辞、領域コード、ロール、出力言語 |
| `.qa/knowledge/` | | 既存機能のナレッジ。画面名・文言の出典として使い、テスト対象にはしない |
| 開発サイズ | | 起動引数の `開発サイズ:`。無ければ Step 1 で推定する |
| 開始 Step | | 起動引数の `from: step1 / step2 / step3`。既定は step1 |

## フロー

```
Step 1 テスト分析 ─→ ⛔ゲート1 ─(「Step 2 の出力をしてください」)→ Step 2 観点生成
  ─→ check_viewpoints ─→ ⛔ゲート2 ─(「Step 3 の出力をしてください」)→ Step 3 ケース生成
  ─→ check_testcases ─→ 完了報告
```

各 Step では、次の順に進める。

1. **その Step に入ってから**、対応する reference を読む。次の Step の reference は先に読まない。読み込みを Step ごとに区切ることで、コンテキストを今の作業に集中させる。
2. reference の「契約」にある入力を読み、assets の雛形どおりに成果物を Write する。
3. 契約に検査があれば、スクリプトを実行する。
4. 次のゲートか完了報告へ進む。

| Step | reference | 雛形 | 成果物 |
| --- | --- | --- | --- |
| 1 | [references/step1-test-analysis.md](references/step1-test-analysis.md) | `assets/step1-analysis.template.md` | `step1-analysis.md` |
| ゲート1・2 | [references/gate-protocol.md](references/gate-protocol.md) | — | — |
| 2 | [references/step2-viewpoint-design.md](references/step2-viewpoint-design.md) | `assets/step2-viewpoints.template.md` | `step2-viewpoints.md` |
| 3 | [references/step3-test-case-generation.md](references/step3-test-case-generation.md) | `assets/step3-testcases.template.md` | `step3-testcases.md` |

reference・assets・scripts のパスは、この skill のディレクトリからの相対パスである。成果物のパスは、作業ディレクトリからの相対パスである。

### 再開

- `from: step2` のように指定されたら、その Step から始める。前の Step の成果物が `output/{ID}/` に無ければ、無いことを伝えて止まる。
- 指定が無くても `output/{ID}/` に成果物が既にあるときは、上書きする前に「どの Step から再開するか」を QA に確かめる。QA が直した成果物を黙って上書きしないためである。

### ゲート

ゲートの表示項目と自己チェックの手順は `references/gate-protocol.md` に従う。要点は次のとおり。

- ゲートでは決められた項目だけを表示して、**ターンを終える**。次に進めるのは QA の合図だけである。
- 修正の指示を受けたら、差分 Edit で直し、同じゲートの表示をもう一度出して止まる。
- 自己修正をしてよいのは、ゲート2 の前の `BOLD` と `HEADING` だけで、1 回までである。

### 検査スクリプト

標準ライブラリだけで動き、ファイルを書き換えない。`--json` を付けるとレシートを返す。報告は必ずレシートの `status` と `findings` を根拠にする。実行していない検査を「OK」と言わない。

```bash
python3 <skill>/scripts/check_viewpoints.py output/{ID}/step2-viewpoints.md --json
python3 <skill>/scripts/check_testcases.py output/{ID}/step3-testcases.md --viewpoints output/{ID}/step2-viewpoints.md --json
```

終了コードは 0=OK、1=指摘あり、2=入力エラー。`check_testcases.py` は観点ファイルから必要なケース数を数え直し、足りない TP を `TRACE` として返す。Step 3 自身が書いたトレース表は信用しない。

### 完了報告

Step 3 の検査の後、次だけを報告して終える。

1. 成果物 3 つのパス
2. `check_testcases.py` のレシートの結果（ケース数、最終ケース ID、指摘があればその一覧）
3. 指摘が残っている場合は、自分で直さずにその旨を書く。Step 3 の後には自己修正のゲートが無い
4. Step 3 の途中で気づいた観点の抜け（あれば）

## Common Rationalizations

| 言い訳 | 実際 |
| --- | --- |
| 「内容に自信があるので、ゲートを飛ばして続けて出す」 | ゲートの目的は、AI が自分では見つけられない読み違いを人が止めることである。自信があるかどうかは関係ない |
| 「`[要確認]` は文脈から推測できるので埋めておく」 | もっともらしい推測は、レビューをすり抜ける誤りの典型である。QA の回答があるまで残す |
| 「期待結果は太字セルを少し言い換えた方が読みやすい」 | 言い換えると、観点とケースの対応を機械的に確かめられなくなる。そのまま写す |
| 「観点の表の行が多いので、似たケースはまとめる」 | 表の 1 行が 1 ケース以上、という約束がトレース検査の前提である。まとめると `TRACE` で落ちる |
| 「検査は形式チェックだけなので、走らせなくても大丈夫」 | 太字漏れ・連番・行数は人の目で見落としやすい。だから機械で見る |

## Red Flags

- QA の合図が無いのに、次の Step の reference を読んだ、またはファイルを書いた
- ゲートで、決められた項目以外（要約・所感・補足）を表示した
- `[要確認]` が理由なく消えている
- 期待結果に、Step 2 に無い文言がある
- レシートを見ずに「検査 OK」と報告した
- シェルのリダイレクトで成果物を書いた

## Verification

完了報告の前に確かめる。

- [ ] `output/{ID}/` に `step1-analysis.md`・`step2-viewpoints.md`・`step3-testcases.md` がある
- [ ] ゲート1・ゲート2 のそれぞれで、QA の合図を受けてから次へ進んだ
- [ ] `check_viewpoints.py` をゲート2 の前に実行し、レシートを確認した
- [ ] `check_testcases.py --viewpoints` を実行し、そのレシートの内容をそのまま報告した
