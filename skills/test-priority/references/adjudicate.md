# adjudicate — 人の裁定を記録する

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | QA の指示（どのケースを、どの重要度か規模にするか、その理由） |
| 出力 | `output/test-priority/adjudications.json`（`adjudicate.py` が書く） |
| 検査 | `adjudicate.py` が、ケースの存在・値の語彙・理由の有無を検査する |
| 次 | `update`（`references/update.md`）で結果に反映する |

## 手順

1. QA の指示から、次の 3 つを決める。足りないものは QA に聞く（推測しない）。
   - 対象のケース（ケース番号）
   - 変える値：重要度（`R1`〜`R4`）か規模（`sanity` `smoke` `light` `full` `対象外`）のどちらか、または両方
   - 理由（必須。後で見直す人のために、1 文で書いてもらう）
2. 次を実行する。
   ```bash
   python3 <skill>/scripts/adjudicate.py <ケース> --level R2 --reason "<理由>" --config .qa/test-priority.toml
   ```
   規模を決めるときは `--scale smoke` のように指定する。終了コードが 2 なら、メッセージを QA に見せて止まる。
3. 裁定を消すときは `adjudicate.py --remove <ケース>` を実行する。
4. 続けて `update` を実行して、結果に反映する。

## ルール

- 重要度だけを決めたときは、規模は表から再計算される。規模を決めたときは、その値が使われる。
- 判定不可のケースは、重要度の裁定で判定できるようになる。
- `adjudications.json` を Edit や Write で直接書かない。
- 裁定は `build` でも消えない。
