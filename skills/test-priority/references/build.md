# build — 全ケースを判定する

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `.qa/test-priority.toml`、テストケースの表、`adjudications.json`（あれば） |
| 出力 | `output/test-priority/` の `import.csv` `review.csv` `manifest.json` と `_raw/` |
| 検査 | `check_priority.py`（`finish.py` が実行する） |
| 次 | 完了報告（SKILL.md） |

## 手順

各段で、必要な reference だけを、その段に入ってから読む。

| 段 | 誰が | 内容 |
| --- | --- | --- |
| 1 load | スクリプト | テストケースを読む。前回の判断を消す |
| 2 judge | AI | 全ケースの意味の判断を下書きに書き、取り込む（`references/judge.md`） |
| 3 decide | スクリプト | 重要度・規模を計算する |
| 4 explain | AI | 全ケースの理由文を下書きに書き、取り込む（`references/explain.md`） |
| 5 export | スクリプト | CSV を書く |
| 6 finish | スクリプト | 検査に通れば manifest.json を書く |

1. **load**：`python3 <skill>/scripts/load_cases.py --config .qa/test-priority.toml --fresh` を実行する。終了コードが 2 なら、メッセージを QA に見せて止まる（設定が無ければ `init` を勧める）。件数を控える。
2. **judge**：`python3 <skill>/scripts/plan.py judge --config .qa/test-priority.toml` を実行する（`--fresh` の後なので、全ケースが対象になる）。続けて `references/judge.md` を読み、`_raw/pending.jsonl` の全ケースの判断を下書き `output/test-priority/_raw/judge.draft.jsonl` に書き、取り込む。
3. **decide**：`python3 <skill>/scripts/decide.py --config .qa/test-priority.toml` を実行する。出力（1 ケース 1 行の JSON）が、explain の入力になる。終了コードが 2 のとき、メッセージが「判断が無い、または古いケース」の一覧なら、その一覧のケースだけを下書きに書いて取り込み直し（1 回まで）、decide をやり直す。それ以外のメッセージなら、見せて止まる。
4. **explain**：`python3 <skill>/scripts/plan.py explain --config .qa/test-priority.toml` を実行する（全ケースが対象になる）。続けて `references/explain.md` を読み、`_raw/explain_input.jsonl` の全ケースの理由文を下書き `output/test-priority/_raw/explain.draft.jsonl` に書き、取り込む。
5. **export**：`python3 <skill>/scripts/export.py --config .qa/test-priority.toml` を実行する。「理由が無い」で止まったら、そのケースだけ explain をやり直す（1 回まで）。
6. **finish**：`python3 <skill>/scripts/finish.py --config .qa/test-priority.toml` を実行する。
   - 終了コード 0：manifest.json が書かれた。完了報告へ
   - 終了コード 1：検査の指摘が JSON で出る。指摘のケースだけを直して手順 5 から 1 回だけやり直す。それでも通らなければ、直さずに指摘を QA に報告して止まる。manifest.json は書かれていない
7. 完了報告のために、`python3 <skill>/scripts/check_priority.py --config .qa/test-priority.toml --json` を実行し、`stats` を控える。

## ルール

- `adjudications.json` は読むだけで、書き換えない（裁定を記録するのは `adjudicate`。`references/adjudicate.md`）。
- 判定不可のケースは、判断（judge）も理由文（explain）も他のケースと同じように書く。理由文には、決められない理由と、人に決めてほしいことを書く。
- CSV は `export.py` が書く。Write や Edit で直接書かない。
- 下書きファイルは Write で書く。シェルのリダイレクトで書かない。
