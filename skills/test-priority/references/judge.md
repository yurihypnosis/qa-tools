# judge — 意味の判断を下書きに書く

## 契約

| 項目 | 内容 |
| --- | --- |
| 入力 | `output/test-priority/_raw/cases.jsonl`（1 ケース 1 行：`case` `title` `area` `feature` `screen` `existing` `body`） |
| 出力 | 下書き `output/test-priority/_raw/judge.draft.jsonl` → `apply_judgments.py judge` で `judgments.jsonl` に取り込む |
| 検査 | `apply_judgments.py` が、語彙・ケースの存在・キーを検査する（1 行でも誤りがあれば何も書かない） |
| 次 | decide（`build.md` の手順 3） |

## ロール

QA エンジニアとして、テストケース 1 件が「何を確かめていて、壊れると何が起きるか」だけを判断する。重要度や規模は決めない（スクリプトが計算する）。設定ファイルの重みも読まない。

## 手順

1. `cases.jsonl` を 50 行ずつ読む（Read の offset と limit）。
2. 各ケースを、`title` と `body` に書かれていることだけを根拠に、次の 3 つについて判断する。
3. 下書きに、1 ケース 1 行の JSON を書く。キーは `case` `axes` `impact` `kind` の 4 つだけ。
   ```json
   {"case": "DUMMY-001-TC-001", "axes": ["data"], "impact": "stop", "kind": "応用"}
   ```
4. 全ケースを書き終えたら、次を実行する。
   ```bash
   python3 <skill>/scripts/apply_judgments.py judge output/test-priority/_raw/judge.draft.jsonl --config .qa/test-priority.toml
   ```
   終了コードが 2 なら、メッセージが示す行だけを直して、1 回だけ再実行する。

## 判断 1：リスク軸 `axes`（0 個以上）

本文に根拠がある軸だけを挙げる。同じ軸に何語当たっても 1 つ。根拠が無いのに「念のため」で挙げない（挙げるほど重要度が上がる）。

| 軸 | 当てはまるとき |
| --- | --- |
| `data` | 値が保存・計算・表示で誤る。エラーが出ないまま壊れる |
| `permission` | ロールごとの操作の可否。他人のデータへのアクセス |
| `blast` | 壊れると、他の機能・他のユーザー・他の画面にも波及する |

## 判断 2：影響範囲 `impact`（1 つ）

このケースが確かめている振る舞いが壊れたときに、何が起きるか。迷ったら、重い方を選ぶ（`cosmetic` < `stop` < `harm`）。

| 値 | 当てはまるとき |
| --- | --- |
| `cosmetic` | 見た目・文言・並び順だけが変わる。利用者の作業は止まらない |
| `stop` | 業務の一部ができなくなる、または間違った結果で続けてしまう |
| `harm` | お金・法令・権限に実害が出る（誤請求、情報の漏えい、権限のない操作ができる） |

## 判断 3：種別 `kind`（1 つ）

| 値 | 当てはまるとき |
| --- | --- |
| `代表` | その機能の基本的な正常系の操作を確かめている |
| `応用` | 境界値・異常系・条件の組み合わせを変えたものを確かめている。迷ったらこちら |

## ルール

- `fingerprint` や `reason` は書かない（取り込みスクリプトが補う）。
- 領域・機能・画面から重要度を推測しない。判断するのは上の 3 つだけ。
- 下書きは Write で書く。
