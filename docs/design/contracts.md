# 共通の契約

test-steps・test-priority・code-map・screen-list の 4 つのツールが同じ形で動くための約束ごと。ツールを作るときは、この文書だけを見れば入出力の形が分かるようにする。考え方は [principles.md](principles.md)、ツール同士の受け渡しは [data-flow.md](data-flow.md) にある。

test-case-generator は、この契約より前に作られた。動詞と manifest にはまだ合わせていない（出力の置き場所 `output/` だけは共通）。

## 1. 動詞

- **決めたこと**：1 つのツール = 1 つの skill（`skills/<tool>/`）。引数の最初の語が動詞で、`init` / `build` / `update` / `check` の 4 つだけを使う。そのツールに固有の操作だけ 5 つ目の動詞として足す（例：screen-list の `pair`）
- **理由**：どのツールも同じ 4 語で使えれば、1 つ覚えれば他も使える。途中の段だけを動かしたいときは、動詞を増やさず `build --stage <段>` で指定する

| 動詞 | やること | 書き込むもの |
| --- | --- | --- |
| `init` | 設定を対話で作る。依存ツールも確認する | `.qa/<tool>.toml` |
| `build` | 最初から全体を作る | `output/<tool>/` 全体 |
| `update` | manifest の時点から変わったところだけ作り直す | 変わった項目と manifest |
| `check` | 成果物を検証する。作り直さない | なし（結果を表示するだけ） |

呼び方の例：`/qa-tools:test-steps build`、`/qa-tools:code-map build --stage extract`、`/qa-tools:screen-list update --local`

skill の中の置き方：SKILL.md には流れと動詞の分岐だけを書き、動詞ごとの手順は `references/<verb>.md` に置く。references は SKILL.md から 1 階層だけ参照する。

## 2. 最後の check

- **決めたこと**：`build` と `update` は、最後に必ず `check` と同じ検査を通す。1 つでも失敗したら `manifest.json` を書き換えない
- **理由**：失敗した成果物の時点を「前回」として記録すると、次の `update` が壊れた状態から差分を取ってしまう。manifest が古いまま残っていれば、次の update が同じ範囲をもう一度作り直せる

## 3. 設定

- **決めたこと**：利用側プロジェクトの `.qa/<tool>.toml` に書く。最上位のキーは次の 4 つだけ。個人の環境に依存する値（ローカルの絶対パスなど）は `.qa/local.toml` に分け、利用側の `.gitignore` に入れる
- **理由**：4 つのキーがそろっていれば、どのツールの設定も同じ順に読める。個人のパスを共有の設定に混ぜると、他の人の環境で動かなくなる

| キー | 意味 | 例 |
| --- | --- | --- |
| `source` | 何を読むか。他のツールの出力を読むときは `source.inputs` | `spec_glob = "e2e/**/*.spec.ts"` |
| `output` | どこに何を出すか | `dir = "output/test-steps"` |
| `platform` | どう描くか（ツールごとの描き方の選択） | `"web-react"` |
| `checks` | 何で検証するか | `[[checks]] coverage = { mode = "exact" }` |

`local.toml` には、`[repos]` の下に「名前 = 絶対パス」を書く。共有の設定は `repo = "dummy-app"` のように名前で参照する。

```toml
# .qa/local.toml（git に入れない）
[repos]
dummy-app = "/Users/me/work/dummy-app"
```

## 4. 出力の置き場所

- **決めたこと**：利用側プロジェクトの `output/<tool>/`。プラグインのディレクトリには書かない
- **理由**：test-case-generator が `output/{PBI ID}/` に書いているので、それに合わせる。プラグインのディレクトリは読み取り専用で読み込まれることがある

```
output/
├── DUMMY-001/          test-case-generator（PBI ごと）
├── test-steps/         manifest.json ＋ 手順書 *.md ＋ index.md
├── test-priority/      manifest.json ＋ 取り込み用 CSV ＋ レビュー用 CSV
├── code-map/           manifest.json ＋ KB
└── screen-list/        manifest.json ＋ screens.csv
```

## 5. manifest.json

- **決めたこと**：すべての `output/<tool>/` に、同じ形の `manifest.json` を 1 つ置く。これが成果物の身元書きで、`update` の起点になる
- **理由**：ツールごとに身元書きの形が違うと、鮮度の確認と差分の計画をツールごとに書くことになる

```json
{
  "tool": "screen-list",
  "version": 1,
  "source": { "repo": "dummy-app", "commit": "3f2a9c1" },
  "config_hash": "sha256:9b1e…",
  "inputs": { "code-map": { "commit": "3f2a9c1" } },
  "generated_at": "2026-10-09T10:00:00+09:00",
  "generated_by": { "claude": 6, "local": 0, "script": 2 },
  "items": 8
}
```

| 項目 | 内容 |
| --- | --- |
| `tool` / `version` | ツール名と manifest の形の版（今は 1） |
| `source` | 入力が git なら `repo` と `commit`。ファイルなら `files`（パスのグロブ）と `hash`（内容をまとめたハッシュ） |
| `config_hash` | `.qa/<tool>.toml` のハッシュ。`local.toml` は含めない（人によって違うため） |
| `inputs` | 他のツールの出力を読んだとき、その manifest の `source` を写したもの。入力の地図が古くなっていないかを確かめるのに使う |
| `generated_by` | 項目を誰が作ったかの件数（AI・ローカル LLM・スクリプト・前回からの引き継ぎは `carried`） |
| `items` | 成果物の項目数（手順書の本数、CSV の行数、モジュール数） |

読み書きは `core/manifest.py` だけが行う。

## 6. check の結果

- **決めたこと**：検査スクリプトは、既存の `skills/test-case-generator/scripts/` と同じ JSON レシートを返す。終了コードは 0=OK / 1=指摘あり / 2=入力エラー
- **理由**：skill はレシートの `status` だけで次に進むかを決められる。指摘の中身は `findings` に行番号付きで入るので、人も AI も直す場所が分かる

```json
{
  "check": "check_steps",
  "file": "output/test-steps",
  "status": "fail",
  "findings": [
    { "code": "SECTION", "file": "e2e/login.md", "line": 12, "section": "補足" }
  ],
  "stats": { "documents": 3, "unresolved": 2 }
}
```

`findings` の各要素は、`code`（大文字の短い識別子）と、場所を示す `file` / `line` を必ず持つ。

## 7. core の置き場所

- **決めたこと**：ツールをまたいで使う処理は、プラグイン直下の `core/` に置く。skill からは `python3 <skill>/../../core/<name>.py` で呼ぶ
- **理由**：プラグインの中の配置（`skills/<tool>/` の 2 階層上がプラグインの直下）は変わらないので、相対パスで届く。この相対パスはテストで確かめる
- **切り出す時期**：2 つ目のツールが同じ処理を必要としたときに core に移す。1 つ目のツールしか使わないうちは、そのツールの `scripts/` に置く

| モジュール | やること | 最初に使うツール |
| --- | --- | --- |
| `core/manifest.py` | manifest.json の読み書き、設定のハッシュ | test-steps |
| `core/plan.py` | manifest の commit から今までの変更ファイルを列挙する | test-steps |
| `core/carry.py` | 前回の行を「キー ＋ 内容のハッシュ」で引き継ぎ、裁定を記録する | test-priority |
| `core/screen_id.py` | 画面 ID の発行と逆引き | screen-list |

## 8. 実行環境

- **決めたこと**：Python 3.11 以上、標準ライブラリだけ。テストは `unittest`（pytest は使わない）
- **理由**：TOML を読む `tomllib` が 3.11 から標準に入った。利用側で `pip install` を求めないので、プラグインを入れればそのまま動く

## 完了の定義

ツールの `build` を作る Issue は、次がそろって完了とする。

1. テストが通る：`python3 -m unittest discover -s tests -t .`
2. マニフェストの検証が通る：`claude plugin validate .`
3. ダミー製品で E2E を 1 回以上動かし、出力を `examples/dummy-product/sample-output/<tool>/` に残す
4. `skills/<tool>/evals/evals.json` に挙動評価のケースを 2 つ以上足す
5. README の「構成」と使い方、必要なら `docs/architecture/` の図を更新する
6. `.claude-plugin/plugin.json` の `version` を上げる
