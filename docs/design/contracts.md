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
| C3 | 設定ファイル | `.qa/<ツール名>.toml`。最上位のキーは `source` / `output` / `platform` / `checks` の 4 つと、判定の規則を持つツールだけが使う `rules` |
| C4 | 出力ディレクトリ | `output/<ツール名>/`。ツールはここ以外に書かない |
| C5 | manifest.json | 8 つのキーを持つ JSON |
| C6 | 検査結果 | 既存の検査スクリプトと同じ形の JSON。終了コードは 0 / 1 / 2 |
| C7 | core の呼び方 | `core/` はプラグイン直下。スクリプトからは `parents[3] / "core"` を import パスに足す |
| C8 | 実行環境 | Python 3.11 以上、標準ライブラリだけ、テストは unittest |
| C9 | プラットフォーム定義 | アプリの種類で変わる処理は `skills/<ツール名>/platforms/<名前>/` の下にだけ置く |

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
2. 最上位のキーは次の表のものだけ。ツールごとに違うのは、各キーの下の中身。`rules` は、判定の規則（重み・しきい値など）を持つツールだけが使う

| キー | 意味 | 例（code-map でサンプルアプリを読む） |
| --- | --- | --- |
| `source` | 何を読むか | `repo = "sample-app"`、`root = "src"` |
| `output` | どこに書くか | `dir = "output/code-map"` |
| `platform` | どのプラットフォーム定義を使うか（C9） | `["typescript"]` |
| `checks` | どの検査を実行するか。型は表で固定：`run` に検査の名前の配列を書き、検査ごとの設定が要るときは `[checks.<名前>]` に書く | `[checks]` の下に `run = ["public-files"]` |
| `rules` | どう決めるか。判定の規則を持つツールだけが使う。中身はツールの仕様書で決める | test-priority の `[rules.areas.<領域コード>.weights]`（[仕様](tools/test-priority.md)） |

3. `source.repo` は、読むソースがどこにあるかを名前で指す
   - 利用側プロジェクトそのものを読むときは `repo = "."`
   - 別のリポジトリを読むときは名前を書き（例：`repo = "sample-app"`）、その絶対パスを**個人設定ファイル** `.qa/local.toml` に書く。共有の設定ファイルに絶対パスを書くのは禁止

```toml
# .qa/local.toml（git に入れない）
[repos]
sample-app = "/Users/me/work/sample-app"
```

4. 設定ファイルが無い、キーが足りない、または `platform` の値に対応するプラットフォーム定義が無いときは、既定値で続けずに止まり、`init` を実行するよう伝える

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
  "source": { "repo": "sample-app", "commit": "3f2a9c1" },
  "config_hash": "sha256:9b1e0c…",
  "inputs": { "code-map": { "repo": "sample-app", "commit": "3f2a9c1" } },
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
| `core/carry.py` | 前回の項目を「キー ＋ 内容のハッシュ」で比べて引き継ぐ。裁定の記録 | test-priority（#15） |
| `core/jsonl.py` | JSON Lines の読み書き（キーをソートして、同じ入力なら同じバイト列にする） | test-priority |
| `core/config.py` | 設定ファイルの読み込みと、`source.repo` の名前から場所を引く（`.qa/local.toml`） | code-map |
| `core/gitinfo.py` | ソースのコミット（未コミットの変更があれば `+dirty`） | code-map |

## C8. 実行環境

**ルール（必須）**：Python 3.11 以上、標準ライブラリだけを使う。テストは `unittest` で書く（pytest は使わない）。

**理由**：設定ファイルを読む `tomllib` は Python 3.11 から標準ライブラリにある。標準ライブラリだけなら、利用側で `pip install` が要らない。

## C9. プラットフォーム定義

**ルール（必須）**

1. アプリの種類（言語・フレームワーク・テストケースの形式）によって変わる処理は、`skills/<ツール名>/platforms/<プラットフォーム名>/` の下にだけ置く。それ以外の場所（SKILL.md、references/、scripts/、core/）には、特定の言語やフレームワークの名前と処理を書かない
2. 設定ファイルの `platform` キーで、使うプラットフォーム定義を選ぶ。存在しない名前なら止まる（C3 の 4）
3. 新しいアプリの種類に対応するときは、`platforms/` の下にディレクトリを 1 つ足すだけで済むようにする。共通部分を書き換える必要が出たら、先に共通部分を直す PR を出す
4. `init` で選べるプラットフォームは、`platforms/` のディレクトリ一覧を読んで人に見せる。SKILL.md や references/ に選択肢を書かない

**確かめ方**：`skills/<ツール名>/` の中の `platforms/` 以外と `core/` を、プラットフォーム名（例：`nextjs`、`typescript`）で grep して 0 件であること

**各ツールのプラットフォーム定義が用意するもの**

| ツール | `platform` で選ぶもの | プラットフォーム定義が用意するもの | 最初に作るもの |
| --- | --- | --- | --- |
| code-map | 言語（複数可。`platform = ["typescript", "python"]`） | import の抜き出し方、シンボルの抜き出し方、別名の解決（tsconfig の `paths` など） | `typescript`、`python` |
| screen-list | UI フレームワーク（1 つ） | 画面の候補の列挙（`candidates.py`。1 行 = 画面のキー・ファイル・行・URL があれば URL）、画面 ID の接頭辞、網羅チェックの期待集合 | `nextjs-app-router` |
| test-priority | テストケースの形式（1 つ） | テストケースの読み方（CaseNo・タイトル・事前条件・手順・期待結果・確認画面の列の対応） | `tcg-markdown`（test-case-generator の 15 列の表） |

**理由**：アプリの種類ごとの違いを 1 か所に閉じ込めれば、サンプルアプリを替えても、新しい種類のアプリに広げても、共通部分は変わらない。

## 完了の定義

ツールの `build` を作る Issue は、次の 6 つがすべて満たされたら完了とする。

1. `python3 -m unittest discover -s tests -t .` が通る
2. `claude plugin validate .` が通る
3. E2E を 1 回以上実行し、出力例を置く。ソースコードを読むツールはサンプルアプリで実行し `examples/sample-app/sample-output/<ツール名>/` に、テストケースを読むツールは `examples/dummy-product/` で実行し `examples/dummy-product/sample-output/<ツール名>/` に置く
4. `skills/<ツール名>/evals/evals.json` に挙動評価のケースを 2 つ以上書く
5. README の「構成」と使い方を更新する。ツールの受け渡しが変わったら `docs/architecture/` の図も更新する
6. `.claude-plugin/plugin.json` の `version` を上げる
