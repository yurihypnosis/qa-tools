# update — 変わったケースだけ判定し直す

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `.qa/test-priority.toml`、テストケースの表、前回の出力（`_raw/judgments.jsonl` と `manifest.json`）、`adjudications.json`（あれば） |
| 出力 | `output/test-priority/` の `import.csv` `review.csv` `manifest.json`。変わっていないケースの行は、前回と 1 バイトも変わらない |
| 検査 | `check_priority.py`（`finish.py` が実行する） |
| 次 | 完了報告（SKILL.md） |

## 何が引き継がれ、何がやり直されるか

| 変わったもの | やり直すもの |
| --- | --- |
| ケースの内容（タイトル・領域・機能・画面・事前条件・手順・期待結果）が変わった、または新しいケース | AI の判断（judge）と理由文（explain） |
| 設定ファイルの規則（重み・リスク軸・既定値・除外）が変わった | 重要度・規模の計算（スクリプト。全ケースで必ずやり直す）。計算の結果、重要度が変わったケースの理由文だけ |
| 人の裁定が変わった | 同じ（計算と、重要度が変わったケースの理由文） |
| 何も変わらない | 何もしない。出力は前回と同じ |

AI が判断を作るのは、`plan.py` が挙げたケースだけである。それ以外のケースは、前回の判断をそのまま使う（P6）。

## 手順

1. 前回の出力が無い（`_raw/judgments.jsonl` か `manifest.json` が無い）なら、`build` を使うよう伝えて止まる。
2. `python3 <skill>/scripts/load_cases.py --config .qa/test-priority.toml` を実行する（`--fresh` は付けない）。終了コードが 2 なら、メッセージを見せて止まる。
3. `python3 <skill>/scripts/plan.py judge --config .qa/test-priority.toml` を実行する。出力の `pending`（判断し直すケース）、`carried`（引き継ぐ件数）、`removed`（入力から消えたケース）を控える。
4. `pending` が空でなければ、`references/judge.md` を読み、`_raw/pending.jsonl` のケースだけ判断して取り込む。空なら、この手順は飛ばす。
5. `python3 <skill>/scripts/decide.py --config .qa/test-priority.toml` を実行する（終了コードが 2 のときは `build.md` の手順 3 と同じ）。
6. `python3 <skill>/scripts/plan.py explain --config .qa/test-priority.toml` を実行する。`pending` が空でなければ、`references/explain.md` を読み、`_raw/explain_input.jsonl` のケースだけ理由文を書いて取り込む。空なら、飛ばす。
7. `export.py` を実行し、続けて `finish.py` を実行する（`build.md` の手順 5・6 と同じ）。
   - 検査が `ADJUDICATION_UNKNOWN_CASE` で止まったら、入力から消えたケースに裁定が残っている。裁定を消してよいか QA に確かめ、よければ `adjudicate.py --remove <ケース>` で消して、手順 7 をやり直す。
8. 完了報告のために `check_priority.py --config .qa/test-priority.toml --json` を実行する。

## 完了報告

SKILL.md の完了報告に加えて、次を報告する。

1. 判断し直したケースの件数と、そのケース（5 件まで。多ければ件数だけ）
2. 引き継いだ件数
3. 理由文だけ書き直したケースの件数（重要度が変わったもの）
4. 入力から消えたケース

## ルール

- `plan.py` が挙げたケース以外の判断・理由文を、書き直さない。
- 前回の出力と見比べて、変わっていないケースの行が変わっていないことを確かめる（`review.csv` の同じ行を比べる）。
