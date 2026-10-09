# ツール同士の受け渡し

どのツールが、他のどのツールの出力を読むかを決める。ここに書いていない読み方はしない（[principles.md](principles.md) の P8）。言葉の定義は [glossary.md](glossary.md) にある。

- **状態**：v0.4.0 時点の決定。表に出てくるツールのうち、実装済みは test-case-generator だけ
- **変えるとき**：表を変える PR を先に出し、マージしてから読む側を実装する

![ツール同士の受け渡し](../architecture/data-flow.png)

## 公開ファイルの一覧

他のツールが読んでよいのは、この表のファイル（と列）だけである。

| ID | 読むツール | 作るツール | 公開ファイル | 読んで何をするか |
| --- | --- | --- | --- | --- |
| F1 | screen-list | code-map | `output/code-map/lookup/routes.jsonl` | ルート定義の一覧から、画面の候補を列挙する |
| F2 | screen-list | code-map | `output/code-map/manifest.json` | 読んだ routes.jsonl が古くないかを確かめる |
| F3 | test-steps | screen-list | `output/screen-list/screens.csv` の `画面ID` 列と `URL` 列 | spec の `page.goto(URL)` の URL から画面 ID を引き、手順書の各ステップに書く |
| F4 | test-steps | code-map | `output/code-map/lookup/tree.md` | screens.csv の `ソース` 列のファイルが、どのモジュールに属するかを引く |
| F5 | test-priority | test-case-generator | `output/*/4-testcases.md` の 15 列の表 | 判定するテストケースの一覧として読む |
| F6 | test-priority | test-steps | `output/test-steps/**/*.md`（`index.md` を除く） | 自動テストの手順書を、手動のテストケースと同じ基準で判定する |
| F7 | test-priority | screen-list | `output/screen-list/screens.csv` の `画面ID` 列と `画面名` 列 | テストケースの「確認画面」列の画面名から画面 ID を引く |

**読み合わないこと（決定）**：code-map は screen-list の出力を読まない。読み合うと、どちらを先に `update` しても、片方が 1 つ前の版を読むことになるからである。「このモジュールに含まれる画面」が必要なツールは、F3 と F4 を自分で突き合わせて求める。

## 画面 ID

| 決めたこと | 内容 |
| --- | --- |
| 作るのは | screen-list だけ。他のツールは screens.csv から引くだけで、自分で作らない |
| 作り方（画面） | `web/` ＋ ルート定義のパス（先頭の `/` を除く）。例：ルート `/tasks/new` → `web/tasks/new` |
| 作り方（ダイアログ） | 開く画面の ID ＋ `#` ＋ ダイアログのコンポーネント名。例：`web/tasks#DeleteTaskDialog` |
| 変わらないこと | 画面名を変えても ID は変わらない。ルートのパスかコンポーネント名を変えたときだけ変わる |
| 引けないとき | 他のツールで画面 ID を決められないときは `[未解決: 画面を特定できない]` と書く（P5） |

画面 ID でつなぐと、次の 3 つの問いに答えられる。

1. この画面は、どのモジュールで実装されているか（F3 ＋ F4）
2. この画面を確かめているテストはあるか（F3、F7）
3. どのテストにも出てこない画面はどれか（#27 で作る）

## update を実行する順番

ソースコードが変わったら、次の順に `update` を実行する。後のツールが、前のツールの新しい出力を読めるようにするためである。

1. `/qa-tools:code-map update`
2. `/qa-tools:screen-list update`
3. `/qa-tools:test-steps update`
4. `/qa-tools:test-priority update`

各ツールは `update` を始める前に、自分の manifest の `inputs` と、読む先のツールの今の manifest の `source` を比べる。違っていたら（＝読む先が更新されていたら）、そのことを人に伝えてから進める。

## 役割の分担

「今回の変更で、どのテストまで実行するか」（変更されたファイル → 画面 → テスト）は、code-map と screen-list の出力で絞り込む。テストケースごとに重要度と規模を決める test-priority には、この絞り込みを入れない。
