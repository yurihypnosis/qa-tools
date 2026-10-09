# test-priority の仕様

テストケース 1 件ずつに、**重要度**（壊れたとき困る度合い）と**規模**（どの実行単位で流すか）を、同じ規則で決める。言葉は [glossary.md](../glossary.md)、共通の約束は [contracts.md](../contracts.md) に従う。

- **状態**：未実装（v0.5.0 で実装。Issue #13〜#15）
- **入力**：テストケースの表。最初に対応する形式は test-case-generator の `4-testcases.md`
- **出力**：取り込み用 CSV、レビュー用 CSV、manifest.json（`output/test-priority/`）

## 1. 何を決めるか

| 決めるもの | 値 | 意味 |
| --- | --- | --- |
| 重要度 | `R1` `R2` `R3` `R4` | R1 が最も重要。壊れると、お金・法令・権限に実害が出る、または業務が止まる |
| 規模 | `sanity` `smoke` `light` `full` | そのケースを**含む最小の実行単位**。大きい規模は小さい規模をすべて含む（sanity ⊂ smoke ⊂ light ⊂ full） |
| 対象外 | `対象外` | 設定で除外したケース。取り込み用 CSV に入れない |
| 判定不可 | `判定不可` | 情報が足りず決められないケース。推測せず人に返す（P5） |

test-case-generator の「重要度/Priority」列（High / Medium / Low）は、観点設計での優先度である。test-priority は**この列を書き換えない**。判定の材料として読み、結果は別のファイルに出す。

## 2. 処理の流れ

| 段 | `--stage` | 誰が | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| 読む | `load` | スクリプト | テストケースの表 | 項目の一覧（メモリ上） |
| 判定 | `judge` | AI | 新規・変更のあったケース | `_raw/judgments.jsonl` に 1 件 1 行 |
| 決定 | `decide` | スクリプト | 項目の一覧、judgments.jsonl、設定、adjudications.json | 重要度・規模・代表か・要レビュー |
| 理由 | `explain` | AI | 決定の結果。新規のケースと、`reason_level` が決定した重要度と違うケースだけ | judgments.jsonl の `reason` と `reason_level` |
| 書き出し | `export` | スクリプト | 上のすべて | import.csv、review.csv、manifest.json |

- AI がするのは、意味の判断（リスク軸・影響範囲・代表か応用か・理由文）だけ。重要度と規模は、AI の判断と設定から**スクリプトが計算する**（P3）
- 入力と設定が同じなら、2 回目の出力は 1 バイトも変わらない（P6）。AI の判断は judgments.jsonl に残し、ケースの内容が変わっていなければ使い回す

## 3. 入力：プラットフォーム定義 `tcg-markdown`

共通部分は、テストケースの列名を知らない（C9）。`skills/test-priority/platforms/tcg-markdown/` が、表を次の形の項目に読み替えて返す。

| 項目のキー | 意味 | tcg-markdown での元の列 |
| --- | --- | --- |
| `case` | ケースの識別子。全ファイルで一意 | `CaseNo.` |
| `title` | 確かめる内容 | `タイトル/Title` |
| `area` | 領域コード | `領域/Area` |
| `feature` | 機能名 | `機能/Function` |
| `screen` | 確認する画面の名前 | `確認画面/Screen` |
| `existing` | 既存の優先度（`high` `medium` `low`、無ければ空） | `重要度/Priority`（High / Medium / Low） |
| `body` | 事前条件・手順・期待結果をつなげた文字列 | `事前条件/Precondition` `実施手順/Execution Step` `期待結果/Expected Result` |
| `fingerprint` | 内容のハッシュ（sha256）。引き継ぎ（P6）の判定に使う | `title` `area` `feature` `screen` `body` をつなげたもの |

- 読むファイルは設定の `source.cases_glob`（例：`output/*/4-testcases.md`）で指す
- `case` が複数のファイルで重複したら、止まる（終了コード 2、`DUPLICATE`）

## 4. 重要度の決め方

重要度は次の順で決める。

1. **開始点**：設定の機能の重み表から引く（5.2）
2. **リスク軸と影響範囲**：AI が判断する（4.1）
3. **上げ下げ**：下の表で ±1 段まで。範囲は R1〜R4 に収める
4. **既存の優先度で止める**：`existing` が `high` なら下げない、`low` なら上げない
5. **裁定**：adjudications.json に人の裁定があれば、それを優先する（7）

### 4.1 AI が判断すること

| 判断 | 値 | 基準 |
| --- | --- | --- |
| リスク軸 | `data` `permission` `blast`（0 個以上） | 下の表。当てはまる軸を全部挙げる。同じ軸に何語当たっても 1 つと数える |
| 影響範囲 | `cosmetic` `stop` `harm`（1 つ） | `cosmetic`：見た目だけ。`stop`：業務が止まる／できなくなる。`harm`：お金・法令・権限に実害 |
| 種別 | `代表` `応用`（1 つ） | `代表`：その機能の基本的な正常系の操作。`応用`：境界値・異常系・条件の組み合わせを変えたもの |

| リスク軸 | 当てはまるケース |
| --- | --- |
| `data` | 値が保存・計算・表示で誤る、または静かに壊れる（エラーが出ない） |
| `permission` | ロールごとの操作の可否、他人のデータへのアクセス |
| `blast` | 壊れると他の機能・他のユーザー・他の画面にも波及する |

### 4.2 上げ下げの表

「有効なリスク軸」は、AI が挙げたリスク軸のうち、その領域の設定 `emphasis` に入っているもの。

| 影響範囲 | 有効なリスク軸 | 上げ下げ |
| --- | --- | --- |
| `stop` または `harm` | 1 つ以上 | 1 段上げる |
| `stop` または `harm` | 0 個 | 変えない |
| `cosmetic` | 1 つ以上 | 変えない |
| `cosmetic` | 0 個 | 1 段下げる |

## 5. 設定ファイル `.qa/test-priority.toml`

contracts.md の C3 に従う。判定の規則は `rules`（C3 で追加したキー）に書く。

```toml
platform = "tcg-markdown"

[source]
repo = "."
cases_glob = "output/*/4-testcases.md"

[output]
dir = "output/test-priority"

[rules]
group_by = "screen"            # 代表を 1 件に絞る単位。feature か screen

[rules.areas.DMY-TASK]
emphasis = ["data", "permission"]
default = 3                    # 機能が表に無いときの開始点（R3）

[rules.areas.DMY-TASK.weights]
"タスク名の文字数上限" = 3

[rules.areas.DMY-COMMON]
emphasis = ["permission", "blast"]
default = 2

[rules.areas.DMY-COMMON.weights]
"ログイン" = 1

[rules.exclude]
features = []                  # 規模を「対象外」にする機能名

[checks]
run = ["import-clean", "examples"]
```

### 5.1 `rules` の項目

| キー | 型 | 意味 |
| --- | --- | --- |
| `group_by` | `"feature"` か `"screen"` | 代表を 1 件に絞る単位。その値が空のケースは、グループ名 `(なし)` に入れる |
| `areas.<領域コード>.emphasis` | 配列（`data` `permission` `blast`） | その領域で、重要度を上げる根拠にするリスク軸 |
| `areas.<領域コード>.default` | 整数 1〜4 | 機能が重み表に無いときの開始点（推定になる） |
| `areas.<領域コード>.weights` | 表（機能名 = 整数 1〜4） | 機能ごとの開始点。機能名は `feature` と完全一致 |
| `exclude.features` | 配列 | 規模を `対象外` にする機能名 |

領域コードは `.qa/product.md` の領域コードと同じ値を使う。

### 5.2 開始点の引き方

1. `area` が `rules.areas` に無い → **判定不可**（`[未解決: 領域 <コード> が設定に無い]`）
2. `weights` に `feature` がある → その値
3. 無い → `default`。要レビューの印 `推定` を付ける

## 6. 規模の決め方

### 6.1 代表の選び方

1. ケースを `group_by` の値（`feature` か `screen`）でグループにする
2. グループの中で、種別が `代表` のケースだけを候補にする
3. 候補を「重要度の小さい順（R1 が先）、同じなら `case` の昇順」に並べ、先頭の 1 件を**そのグループの代表**にする
4. 候補が 0 件のグループには、代表がいない

### 6.2 規模の表

| 重要度 | グループの代表 | それ以外 |
| --- | --- | --- |
| R1 | `sanity` | `smoke` |
| R2 | `smoke` | `light` |
| R3 | `light` | `full` |
| R4 | `full` | `full` |

- `exclude.features` に入っている機能のケースは、表によらず `対象外`
- `sanity` に入るのはグループの代表だけなので、グループあたり最大 1 件になる
- 規模は「含む最小の実行単位」なので、入れ子は値の意味で保証される。ケースが smoke に入っていれば、light と full にも入っている

## 7. 人の裁定 `output/test-priority/adjudications.json`

```json
{
  "DUMMY-001-TC-031": { "重要度": "R2", "理由": "管理者の削除は監査対象のため" },
  "DUMMY-001-TC-040": { "規模": "対象外", "理由": "別の PBI で網羅済み" }
}
```

- キーは `case`。`重要度` と `規模` はどちらか、または両方を書ける。`理由` は必須
- `重要度` だけ書いたときは、規模は表（6.2）から再計算する。`規模` を書いたときは、その値を使う
- 判定不可のケースは、裁定で `重要度` を書けば判定できる
- 入力に無い `case` を指していたら、check が `ADJUDICATION_UNKNOWN_CASE` を返す
- 次回以降の実行でも、裁定は残る（上書きしない）

## 8. 出力

### 8.1 取り込み用 `import.csv`（UTF-8 BOM 付き）

| 列 | 値 |
| --- | --- |
| `CaseNo.` | `case` |
| `重要度` | `R1` `R2` `R3` `R4` |
| `規模` | `sanity` `smoke` `light` `full` |

- 規模が `対象外` と `判定不可` のケースは、この CSV に**入れない**（手で消す運用をしない。P4 の検査で 0 件を保証する）
- 列の名前と値は、翻訳しない（取り込み先との約束のため）

### 8.2 レビュー用 `review.csv`（UTF-8 BOM 付き）

入力のケースすべてを 1 行ずつ出す。

| 列 | 内容 |
| --- | --- |
| `CaseNo.` `タイトル` `領域` `機能` `確認画面` | 入力から |
| `既存の優先度` | `existing`（High / Medium / Low、無ければ空） |
| `開始点` | `R1`〜`R4`（判定不可なら空） |
| `リスク軸` | 挙げられた軸。`;` 区切り |
| `影響範囲` `種別` | AI の判断 |
| `代表` | グループの代表に `○` |
| `重要度` `規模` | 決定の結果。判定不可・対象外もここに出る |
| `理由` | AI が書く。1 行目に結論、続けて「何を確認する？／壊れると何が困る？／だからこの重要度」 |
| `要レビュー` | 下の印。`;` 区切り |

要レビューの印は 4 種類。

| 印 | 付く条件 |
| --- | --- |
| `上げ` | 開始点が R1 でないのに、結果が R1 になった |
| `下げ` | 開始点が R4 でないのに、結果が R4 になった |
| `推定` | 機能が重み表に無く、`default` を使った |
| `判定不可` | 5.2 の 1 に当たった |

### 8.3 そのほか

- `manifest.json`（C5）：`generated_by` の `claude` は、今回 AI が 1 回でも出力（判断か理由文）を作ったケースの件数、`carried` は 1 回も作らずに judgments.jsonl から使い回したケースの件数、`script` は 0。`claude` ＋ `carried` ＝ `items`（review.csv の行数）
- `adjudications.json`：7
- `_raw/judgments.jsonl`（中間ファイル。他のツールは読まない）：1 件 1 行。`{"case", "fingerprint", "axes", "impact", "kind", "reason", "reason_level"}`。`reason_level` は理由文を書いたときの重要度

## 9. 検査 `check_priority.py`（C6 の形）

| `code` | 条件 |
| --- | --- |
| `COLUMNS` | import.csv の列が 3 つ（`CaseNo.` `重要度` `規模`）と違う |
| `VALUE` | `重要度` か `規模` が決めた語彙の外 |
| `EXCLUDED_ROW` | import.csv に、対象外・判定不可のケースがある |
| `COVERAGE` | 入力のケースが、review.csv に 1 行ずつ無い（欠けている、または重複） |
| `ADJUDICATION_UNKNOWN_CASE` | 7 の裁定が、入力に無いケースを指している |
| `EXAMPLE` | `[checks.examples]` の計算例が、規則どおりの結果にならない |
| `MANIFEST` | manifest.json が無い、または必須のキーが欠けている |

`stats`：`cases`（入力の件数）、`decided`（import.csv の行数）、`unresolved`（判定不可の件数）、規模ごとの件数。

### 9.1 計算例 `[checks.examples]`

設定ファイルに書く。`decide` の規則（4・6）だけを確かめる（AI の判断は入力として与える）。`level` は `R1`〜`R4`、`scale` は規模の値。

```toml
[checks.examples]
[[checks.examples.case]]
name = "データの正しさで 1 段上がる"
area = "DMY-TASK"
feature = "タスク名の文字数上限"
axes = ["data"]
impact = "stop"
kind = "代表"
existing = "high"
representative = true
expect = { level = "R2", scale = "smoke" }
```

## 10. 計算例（ダミー製品の設定、5 の例）

| # | area / feature | 開始点 | リスク軸 | 影響範囲 | 既存 | 種別・代表 | 重要度 | 規模 | 印 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DMY-TASK / タスク名の文字数上限 | R3 | `data` | `stop` | High | 代表・グループの代表 | R2（R3 から上げ） | `smoke` | なし |
| 2 | DMY-TASK / タスク名の文字数上限 | R3 | なし | `cosmetic` | Medium | 応用 | R4（R3 から下げ） | `full` | `下げ` |
| 3 | DMY-COMMON / ログイン | R1 | `permission` | `harm` | High | 代表・グループの代表 | R1（上限） | `sanity` | なし |
| 4 | DMY-COMMON / ログアウト（表に無い） | R2（default） | `blast` | `stop` | なし | 応用 | R1（R2 から上げ） | `smoke` | `上げ` `推定` |
| 5 | DMY-XXX / （任意） | — | — | — | — | — | — | `判定不可` | `判定不可` |
| 6 | DMY-TASK / タスク名の文字数上限 | R3 | `data` | `stop` | Low | 応用 | R3（Low が上げを止める） | `full` | なし |

## 11. 仮の値（P9）

次の値は、設計時に決めた初期値で、測定していない。DUMMY-001 で E2E を実行して、人の修正が多い箇所を見て見直す。見直す前は、変更しない前提で実装する。

| 値 | 初期値 |
| --- | --- |
| 上げ下げの幅 | ±1 段 |
| 規模の表（6.2） | 上の表のとおり |
| 影響範囲 `cosmetic` のとき、有効なリスク軸が 0 個なら下げる | 下げる |
