# 共通の約束ごと

新しいツールを作るときに、全ツールで同じにしなければならない形（コマンド・設定・出力・記録・検査）を決める。ツールを作る人と AI は、この文書と [glossary.md](glossary.md) だけを見れば入出力の形が分かる。

- **対象**：これから作るツール（test-priority・code-map・screen-list）
- **対象外**：test-case-generator（v0.4.0 より前に作った）。C4 の出力ディレクトリ `output/` だけは同じで、それ以外の約束にはまだ合わせていない
- **ルールの強さ**：「必須」「禁止」は [principles.md](principles.md) と同じ意味。外すときは PR に理由を書く

## 一覧

| ID | 決めること | 決めた内容（1 行） |
| --- | --- | --- |
| C1 | 動詞 | `init` / `build` / `update` / `check` の 4 つだけ |
| C2 | 実行の最後 | `build` と `update` は最後に検査を実行し、失敗したら manifest を書かない |
| C3 | 設定ファイル | `.qa/<ツール名>.toml`。最上位のキーは `source` / `output` / `platform` / `checks` の 4 つだけ |
| C4 | 出力ディレクトリ | `output/<ツール名>/`。ツールはここ以外に書かない |
| C5 | manifest.json | 8 つのキーを持つ JSON |
| C6 | 検査結果 | 既存の検査スクリプトと同じ形の JSON。終了コードは 0 / 1 / 2 |
| C7 | core の呼び方 | `core/` はプラグイン直下。スクリプトからは `parents[3] / "core"` を import パスに足す |
| C8 | 実行環境 | Python 3.11 以上、標準ライブラリだけ、テストは unittest |

---

## C1. 動詞

**ルール（必須）**

1. 1 つのツールは 1 つの skill（`skills/<ツール名>/SKILL.md`）にする
2. 引数の最初の語を動詞とし、`init` / `build` / `update` / `check` の 4 つだけを使う
3. 動詞を増やしてよいのは、そのツールにしかない操作だけ（例：screen-list の `pair`）。途中の段だけを実行したいときは、動詞を増やさず `build --stage <段の名前>` にする
4. SKILL.md には「動詞ごとにどの reference を読むか」だけを書き、手順は `references/<動詞>.md` に書く

| 動詞 | やること | 書き込むファイル | 書き込まないファイル |
| --- | --- | --- | --- |
| `init` | 人に質問しながら設定ファイルを作る。必要な外部コマンドがあるかも確かめる | `.qa/<ツール名>.toml` | `output/` |
| `build` | 出力ディレクトリの中身を全部作り直す | `output/<ツール名>/` の全ファイル | `.qa/` |
| `update` | manifest の `source` から変わった入力に対応する項目だけ作り直す | 変わった項目と manifest.json | 変わっていない項目 |
| `check` | 成果物を検査して結果を表示する | なし | すべて |

**例**：`/qa-tools:test-priority build`、`/qa-tools:code-map build --stage extract`

## C2. 実行の最後

**ルール（必須）**：`build` と `update` は、最後に `check` と同じ検査を実行する。検査結果の `status` が `fail` なら次のようにする。

1. manifest.json を書き換えない（前回の内容のまま残す）
2. 検査結果を人に見せて止まる
3. 自分で直して再実行するのは 1 回まで（test-case-generator のセルフレビューと同じ）

**理由**：manifest が前回のまま残れば、次の `update` が同じ範囲をもう一度作り直せる（principles.md の P4）。

## C3. 設定ファイル

**ルール（必須）**

1. 置き場所は利用側プロジェクトの `.qa/<ツール名>.toml`
2. 最上位のキーは次の 4 つだけ。ツールごとに違うのは、各キーの下の中身

| キー | 意味 | 例（code-map でサンプルアプリを読む） |
| --- | --- | --- |
| `source` | 何を読むか | `repo = "my-learning-app"`、`root = "src"` |
| `output` | どこに書くか | `dir = "output/code-map"` |
| `platform` | どの方式で作るか（ツールごとに選べる値が決まっている） | `"typescript"` |
| `checks` | どの検査を実行するか。型は表で固定：`run` に検査の名前の配列を書き、検査ごとの設定が要るときは `[checks.<名前>]` に書く | `[checks]` の下に `run = ["public-files"]` |

3. `source.repo` は、読むソースがどこにあるかを名前で指す
   - 利用側プロジェクトそのものを読むときは `repo = "."`
   - 別のリポジトリを読むときは名前を書き（例：`repo = "my-learning-app"`）、その絶対パスを**個人設定ファイル** `.qa/local.toml` に書く。共有の設定ファイルに絶対パスを書くのは禁止

```toml
# .qa/local.toml（git に入れない）
[repos]
my-learning-app = "/Users/me/work/my-learning-app"
```

4. 設定ファイルが無い、またはキーが足りないときは、既定値で続けずに止まり、`init` を実行するよう伝える

## C4. 出力ディレクトリ

**ルール（必須）**：ツールが書き込むのは利用側プロジェクトの `output/<ツール名>/` だけ。プラグインのディレクトリには書き込まない（読み取り専用で読み込まれることがある）。

```
output/
├── DUMMY-001/        test-case-generator（PBI ごと。この約束より前からある形）
├── test-priority/    manifest.json、取り込み用 CSV、レビュー用 CSV、adjudications.json
├── code-map/         manifest.json、index.md、modules/、lookup/、_raw/（中間ファイル）
└── screen-list/      manifest.json、screens.csv、adjudications.json
```

## C5. manifest.json

**ルール（必須）**：`output/<ツール名>/manifest.json` に、次の 8 つのキーを持つ JSON を書く。読み書きは `core/manifest.py` だけが行い、ツールが直接書かない。

| キー | 型 | 内容 |
| --- | --- | --- |
| `tool` | 文字列 | ツール名 |
| `version` | 整数 | manifest の形の版。今は `1` |
| `source` | オブジェクト | 入力が git のファイルなら `{"repo": "<名前>", "commit": "<コミット>"}`。git に無いファイルなら `{"files": "<グロブ>", "hash": "sha256:<内容のハッシュ>"}` |
| `config_hash` | 文字列 | 設定ファイル `.qa/<ツール名>.toml` の sha256。個人設定ファイルは含めない（人によって違うため） |
| `inputs` | オブジェクト | 他のツールの公開ファイルを読んだとき、そのツールの manifest の `source` を写したもの。読んでいなければ `{}` |
| `generated_at` | 文字列 | 書いた日時（ISO 8601、タイムゾーン付き） |
| `generated_by` | オブジェクト | 項目を何で作ったかの件数。キーは `claude`（AI）、`script`（スクリプト）、`carried`（前回から引き継ぎ）、`local`（ローカル LLM、experimental） |
| `items` | 整数 | 項目の数。`generated_by` の合計と一致する |

**例**（screen-list、サンプルアプリで build した直後）

```json
{
  "tool": "screen-list",
  "version": 1,
  "source": { "repo": "my-learning-app", "commit": "3f2a9c1" },
  "config_hash": "sha256:9b1e0c…",
  "inputs": { "code-map": { "repo": "my-learning-app", "commit": "3f2a9c1" } },
  "generated_at": "2026-10-09T10:00:00+09:00",
  "generated_by": { "claude": 10, "script": 0, "carried": 0, "local": 0 },
  "items": 10
}
```

**使い方**：`update` は `source.commit` から今のコミットまでの変更を調べる。`inputs` のコミットが、読む先のツールの今の manifest と違えば、入力が古いことを人に伝えてから進める。

## C6. 検査結果

**ルール（必須）**：検査スクリプトは、既存の `skills/test-case-generator/scripts/_markdown.py` の `emit()` と同じ形の JSON を標準出力に 1 行で出す。

| キー | 内容 |
| --- | --- |
| `check` | 検査の名前（スクリプト名から `.py` を除いたもの） |
| `file` | 検査したファイルかディレクトリ |
| `status` | 指摘が 0 件なら `"ok"`、1 件以上なら `"fail"` |
| `findings` | 指摘の配列。各要素は `code`（大文字の短い識別子）と `line`（行番号）を必ず持つ。ディレクトリを検査したときは `file` も持つ |
| `stats` | 件数など、指摘ではない数（任意） |

終了コード：`0` = 指摘なし、`1` = 指摘あり、`2` = 入力エラー（ファイルが無いなど）

```json
{"check": "check_priority", "file": "output/test-priority/import.csv", "status": "fail", "findings": [{"code": "EXCLUDED_ROW", "line": 12, "case": "DUMMY-001-TC-031"}], "stats": {"rows": 47, "unresolved": 2}}
```

## C7. core の呼び方

**ルール（必須）**

1. 2 つ以上のツールが使う処理は、プラグイン直下の `core/<名前>.py` に置く（principles.md の P1）
2. skill の手順から実行するとき：`python3 <skill>/../../core/<名前>.py`（`<skill>` は `skills/<ツール名>/`）
3. ツールのスクリプトから import するとき：先頭で `sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "core"))` を実行する（`skills/<ツール名>/scripts/<名前>.py` から 3 階層上がプラグイン直下）
4. 2 と 3 のパスが正しいことを `tests/` のテストで確かめる

| ファイル | やること | 最初に使うツール（Issue） |
| --- | --- | --- |
| `core/manifest.py` | manifest.json の読み書き、設定ファイルのハッシュ | test-priority（#14） |
| `core/plan.py` | manifest のコミットから今までに変わったファイルの一覧 | code-map（#20） |
| `core/carry.py` | 前回の項目を「キー ＋ 内容のハッシュ」で比べて引き継ぐ。裁定の記録 | test-priority（#15） |
| `core/screen_id.py` | 画面 ID を作る・画面 ID から CSV の行を引く | screen-list（#24） |

## C8. 実行環境

**ルール（必須）**：Python 3.11 以上、標準ライブラリだけを使う。テストは `unittest` で書く（pytest は使わない）。

**理由**：設定ファイルを読む `tomllib` は Python 3.11 から標準ライブラリにある。標準ライブラリだけなら、利用側で `pip install` が要らない。

## 完了の定義

ツールの `build` を作る Issue は、次の 6 つがすべて満たされたら完了とする。

1. `python3 -m unittest discover -s tests -t .` が通る
2. `claude plugin validate .` が通る
3. E2E を 1 回以上実行し、出力例を置く。ソースコードを読むツールはサンプルアプリ（my-learning-app）で実行し `examples/my-learning-app/sample-output/<ツール名>/` に、テストケースを読むツールは `examples/dummy-product/` で実行し `examples/dummy-product/sample-output/<ツール名>/` に置く
4. `skills/<ツール名>/evals/evals.json` に挙動評価のケースを 2 つ以上書く
5. README の「構成」と使い方を更新する。ツールの受け渡しが変わったら `docs/architecture/` の図も更新する
6. `.claude-plugin/plugin.json` の `version` を上げる
