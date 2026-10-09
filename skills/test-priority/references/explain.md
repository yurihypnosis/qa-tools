# explain — 理由文を下書きに書く

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `decide.py` の出力（1 ケース 1 行：`case` `start` `level` `scale` `representative` `marks` `effective_axes` `blocked_by` `adjudicated`）、`_raw/cases.jsonl`、`_raw/judgments.jsonl` |
| 出力 | 下書き `output/test-priority/_raw/explain.draft.jsonl` → `apply_judgments.py explain` で `judgments.jsonl` に取り込む |
| 検査 | `apply_judgments.py` が、ケースの存在と理由が空でないことを検査する |
| 次 | export（`build.md` の手順 5） |

## ロール

QA エンジニアとして、決まった重要度と規模の**理由を、読む人（QA）の言葉で**書く。決まった結果を変えない。結果に納得できなくても、理由を作り変えず、完了報告で伝える。

## 手順

1. `decide.py` の出力を、ケースごとに `cases.jsonl` と `judgments.jsonl` の同じケースと突き合わせる。
2. 各ケースの理由文を書く。形は `assets/reason.template.md` に従う。
3. 下書きに、1 ケース 1 行の JSON を書く。キーは `case` と `reason` の 2 つだけ。理由文の中の改行は `\n` と書く。
   ```json
   {"case": "DUMMY-001-TC-001", "reason": "R2・smoke で毎回確認する。\n何を確認する？：…\n壊れると何が困る？：…\nだからこの重要度：…"}
   ```
4. 次を実行する。
   ```bash
   python3 <skill>/scripts/apply_judgments.py explain output/test-priority/_raw/explain.draft.jsonl --config .qa/test-priority.toml
   ```
   終了コードが 2 なら、メッセージが示す行だけを直して、1 回だけ再実行する。

## 「だからこの重要度」の根拠

理由は、`decide.py` が出した事実だけから書く。重要度が決まった本当の原因と違う説明を、もっともらしく作らない。

| `decide.py` の出力 | 書くこと |
| --- | --- |
| `level` が `start` より小さい（上がった） | `effective_axes` の軸と、影響範囲（`impact`）を理由にする |
| `level` が `start` より大きい（下がった） | 影響範囲が見た目だけで、有効なリスク軸が無いことを理由にする |
| `level` と `start` が同じで `blocked_by` が `existing_low` | 計算では上がるはずだったが、既存の優先度が Low のため上げなかった、と書く |
| `level` と `start` が同じで `blocked_by` が `existing_high` | 計算では下がるはずだったが、既存の優先度が High のため下げなかった、と書く |
| `level` と `start` が同じで `blocked_by` が `null` | 上げ下げの条件に当たらなかったこと（有効なリスク軸が無い、または影響範囲が見た目だけではない）を、`effective_axes` と影響範囲から書く |
| `adjudicated` が `true` | 人が決めた値であることを書く（元の計算は書かない） |

## 書き方のルール

- 1 行目は結論：「重要度と規模 ＋ どう流すか」。例：`R2・smoke で毎回確認する。`
- 2〜4 行目は、`何を確認する？：` `壊れると何が困る？：` `だからこの重要度：` で始める。各 1 文。
- 内部の記号（`data` `permission` `blast` `cosmetic` `stop` `harm`）を書かない。日本語の言葉で書く（データの正しさ、権限の境界、影響の広がり、見た目だけ、業務が止まる、実害）。
- 判定不可のケース：1 行目は `決められない。`。続けて、決められない理由（例：領域が設定に無い）と、人に決めてほしいこと（例：重要度を adjudications.json に書く）を書く。
- 対象外のケース：1 行目に、設定で対象外にしていることを書く。
- `要レビュー` に印があるケース：4 行目に、印の理由を 1 文足す（`上げ`：開始点より上がった理由、`下げ`：開始点より下がった理由、`推定`：機能が重み表に無く、領域の既定値を使ったこと）。
