---
name: test-priority
description: テストケース 1 件ずつに、回帰テストとしての重要度（R1〜R4）と、実行する規模（sanity / smoke / light / full）を決め、取り込み用 CSV・レビュー用 CSV・理由文を出す。AI は意味の判断だけをして、重要度と規模は設定の規則からスクリプトが計算する。Use when the user asks to prioritize, rank, or triage test cases for regression — e.g. 「回帰テストの優先度をつけて」「どのテストを毎回流すか決めて」「smoke に入れるケースを選んで」「テストケースの重要度を判定して」「変わったケースだけ判定し直して」「このケースは R1 にして」. Not for writing test cases (use test-case-generator) or for running tests.
license: MIT
metadata:
  version: "0.5.0"
---

# Test Priority

## Overview

テストケースの表を読み、1 件ずつに次の 2 つを決める。

- **重要度** `R1`〜`R4`：壊れたときに困る度合い（R1 が最も重要）
- **規模** `sanity` ⊂ `smoke` ⊂ `light` ⊂ `full`：そのケースを含む最小の実行単位

AI がするのは意味の**判断**（リスク軸・影響範囲・代表か応用か・理由文）だけである。重要度と規模は、その判断と設定ファイルから**スクリプトが決定する**（計算する）。同じ入力なら、2 回目の出力は 1 バイトも変わらない。

## 言葉

この skill の中では、次の使い分けで書く。

| 言葉 | 意味 | 誰が |
| --- | --- | --- |
| 判断（judge） | ケース 1 件の、リスク軸・影響範囲・種別（代表か応用か）を決めること | AI |
| 決定（decide） | 判断と設定から、重要度・規模・代表・要レビューを計算すること | スクリプト |
| 判定 | 判断と決定を合わせた全体（「全ケースを判定する」） | — |
| 判定不可 | 領域が設定に無いなど、情報が足りず決定できないこと。規模の値でもある | — |

仕様の正本は `docs/design/tools/test-priority.md`、言葉の定義は `docs/design/glossary.md` にある（プラグインのリポジトリ側。利用側プロジェクトには無い）。この skill の手順だけで動くように書いてあるが、迷ったら仕様書に従う。

## When to Use

- 手動・自動を問わず、既にあるテストケースの表に、重要度と規模を付けたいとき
- 設定（機能の重み・リスク軸）を見直して、判定をやり直したいとき
- 使わない場面：テストケースを新しく作る（test-case-generator を使う）、テストを実行する

起動例：`/qa-tools:test-priority build`

## 動詞

| 動詞 | やること | 読む reference |
| --- | --- | --- |
| `init` | 質問に答えて `.qa/test-priority.toml` を作る | [references/init.md](references/init.md) |
| `build` | 全ケースを判定し、CSV 2 つと manifest.json を作る | [references/build.md](references/build.md) |
| `update` | 前回から変わったケースだけを判断し直し、ほかは前回の結果を使い回す | [references/update.md](references/update.md) |
| `adjudicate` | 人が決めた重要度・規模を記録する | [references/adjudicate.md](references/adjudicate.md) |
| `check` | 出力を検査する。作り直さない | 下の「スクリプト」の `check_priority.py` |

その動詞に入ってから、対応する reference を読む。他の動詞の reference は先に読まない。

`build` と `update` は、途中の段で、次の 2 つも読む（AI が書く段の手順）。

| 段 | 読む reference |
| --- | --- |
| judge（意味の判断を下書きに書く） | [references/judge.md](references/judge.md) |
| explain（理由文を下書きに書く） | [references/explain.md](references/explain.md) |

## 入力の契約

作業ディレクトリ（利用側プロジェクトのルート）に次があることを最初に確かめる。足りなければ、何が足りないかを伝えて止まる。

| 入力 | 必須 | 内容 |
| --- | --- | --- |
| `.qa/test-priority.toml` | `init` 以外で必須 | 設定ファイル（書き方は `assets/test-priority.template.toml`） |
| テストケースの表 | ✅ | 設定の `source.cases_glob` で指すファイル |
| `output/test-priority/adjudications.json` | | 人の裁定。`adjudicate.py` で記録する。`build` でも消さず、規則より優先する |

プラットフォーム定義（テストケースの表の形式）は、`platforms/` のディレクトリ名で選ぶ。選べるものは `ls <skill>/platforms/` で調べる。

## 出力

すべて `output/test-priority/` の下に書く（設定の `output.dir`）。

| ファイル | 内容 |
| --- | --- |
| `import.csv` | 取り込み用。ケース・重要度・規模の 3 列。対象外と判定不可は入れない |
| `review.csv` | レビュー用。全ケースを 1 行ずつ。理由と要レビューの印を含む |
| `manifest.json` | 何から・いつ作ったかの記録。検査に通ったときだけ書く |
| `_raw/` | 中間ファイル（`cases.jsonl` `judgments.jsonl`）。他のツールは読まない |

## スクリプト

Python 3.11 以上と標準ライブラリだけで動く（設定ファイルの TOML を読む `tomllib` が 3.11 から標準にあるため。`pip install` は要らない）。`<skill>` は、この SKILL.md があるディレクトリ（skill の読み込み時に示される Base directory）を指す。`python3 <skill>/scripts/<名前>.py --config .qa/test-priority.toml` の形で実行する。終了コードは 0=OK、1=検査の指摘あり、2=設定か入力のエラー。

| スクリプト | やること |
| --- | --- |
| `survey.py` | `init` 用。領域・機能・確認画面ごとの件数を JSON で出す（設定ファイルは要らない） |
| `load_cases.py [--fresh]` | テストケースを読み、`_raw/cases.jsonl` を書く。`--fresh` は前回の判断を消す |
| `plan.py judge\|explain` | `update` 用。判断・理由文をやり直すケースだけを `_raw/pending.jsonl` `_raw/explain_input.jsonl` に書く（`build` も、全ケースを対象にして使う） |
| `apply_judgments.py judge\|explain <下書き>` | AI の下書きを `_raw/judgments.jsonl` に取り込む（fingerprint などは補う） |
| `decide.py` | 判断と設定から、重要度・規模・代表・要レビューを計算して JSON Lines で出す |
| `export.py` | `import.csv` と `review.csv` を書く |
| `check_priority.py [--json] [--no-manifest]` | 出力を検査する。読み取り専用 |
| `adjudicate.py` | 人の裁定を記録する・消す |
| `finish.py` | 検査に通ったときだけ `manifest.json` を書く。`plan.json` に載らなかったケースを「引き継ぎ」と数える |

報告は、必ずスクリプトの出力（終了コードと `--json` のレシート）を根拠にする。実行していない検査を「OK」と言わない。

## 言語

理由文と完了報告は、`.qa/product.md` に「出力言語」があればその言語、無ければ日本語で書く。列名と値（`R1` `smoke` `判定不可` など）は、言語によらず変えない（取り込み先との約束のため）。

## 完了報告

`build` の最後に、次だけを報告して終える。

1. 出力ファイルのパス（`import.csv` `review.csv` `manifest.json`）
2. 規模ごとの件数（`check_priority.py --json` の `stats`）
3. 人が見るべき行：`要レビュー` に印がある行の件数と、印ごとの内訳。判定不可があれば、そのケースと、決めてほしいこと
4. 検査の結果（`status`。指摘があればその一覧）

## Common Rationalizations

| 言い訳 | 実際 |
| --- | --- |
| 「重要度も AI が直接決めた方が早い」 | AI に直接決めさせると、同じケースでも実行のたびに結果が変わる。判断だけを AI に任せ、計算はスクリプトにする |
| 「領域が設定に無いが、近い領域の値で決めておく」 | 推測した値は、正しい値と見分けがつかない。判定不可のまま人に返す |
| 「念のため、リスク軸を多めに挙げておく」 | 軸が多いほど重要度が上がり、R1 が膨らんで、毎回流すケースを選べなくなる。本文に根拠がある軸だけ挙げる |
| 「import.csv に判定不可の行があるので、手で消す」 | 手で消す運用は、混入の原因になる。`export.py` が入れない。入っていたら検査が止める |
| 「検査に通らないが、manifest だけ書いておく」 | manifest が前回のままなら、次の実行が同じ範囲をやり直せる。通っていないものを最新と記録しない |
| 「既存の重要度（High / Medium / Low）と食い違うので書き換える」 | 既存の列は書き換えない。判定の材料にするだけで、結果は別のファイルに出す |
| 「変わっていないケースも、念のため判断し直す」 | 判断し直すと、同じケースでも結果が変わる。`update` は `plan.py` が挙げたケースだけを判断する |

## Red Flags

- 重要度や規模を、スクリプトを通さずに AI が書いた
- `import.csv` や `review.csv` を、Write や Edit で直接書いた（`export.py` が書く）
- 下書きに `fingerprint` や `reason_level` を書いた（取り込みスクリプトが補う）
- `adjudications.json` を `build` で消した、または Edit で直接書いた（`adjudicate.py` で記録する）
- `plan.py` が挙げていないケースを判断し直した、または理由文を書き直した
- 理由文に、`data` `permission` `blast` などの内部の記号を書いた
- 検査のレシートを見ずに「OK」と報告した
- 検査に通らないのに `finish.py` 以外の方法で `manifest.json` を書いた

## Verification

完了報告の前に確かめる。

- [ ] `check_priority.py --json` を最後に実行し、`status` を確認した
- [ ] `finish.py` が成功し、`manifest.json` の `items` が `stats.cases` と一致する
- [ ] 判定不可のケースを、報告に挙げた
- [ ] `adjudications.json` が `build` と `update` の前後で変わっていない（`adjudicate` の操作を除く）
- [ ] `update` では、`plan.py` が挙げたケース以外の行が、前回の `review.csv` と 1 バイトも変わっていない
