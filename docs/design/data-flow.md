# ツールのつながり

4 つのツールが、互いの出力のうち何を受け渡すかを決める。ツールごとの詳しい仕様は `tools/<tool>.md`（各マイルストーンの最初の Issue で書く）に置き、ここには受け渡しだけを書く。

![ツールのつながり](../architecture/data-flow.png)

## 受け渡しの表

他のツールが読んでよいのは、この表の「契約のファイル」だけである（[principles.md](principles.md) の原則 8）。表に無いファイルを読む必要が出たら、先にこの表と作る側の契約を更新する。

| 読む側 | 作る側 | 契約のファイル | 何に使うか |
| --- | --- | --- | --- |
| screen-list | code-map | `output/code-map/lookup/routes.jsonl` | 画面の候補を列挙し、グループに分ける |
| screen-list | code-map | `output/code-map/manifest.json` | 入力の KB が古くないかを確かめる |
| test-steps | screen-list | `output/screen-list/screens.csv`（画面ID・URL 列） | 手順の各ステップに「今いる画面 ID」を書く |
| test-priority | test-case-generator | `output/*/4-testcases.md`（15 列の表） | 判定するテストケースの一覧 |
| test-priority | test-steps | `output/test-steps/**/*.md` | 自動テストも、手動のケースと同じ基準で判定する |
| test-priority | screen-list | `output/screen-list/screens.csv`（画面ID・画面名列） | 「確認画面」列を画面 ID に引き、代表を選ぶ単位にする |

code-map は screen-list の出力を読まない。読み合うと、update の順番によってどちらかが 1 つ前の版を読むことになる。「このモジュールに含まれる画面」が知りたいときは、読む側が screens.csv のソース列と code-map の `lookup/tree.md` を突き合わせて引く（原則 8：使う側が変換する）。

## 画面 ID

- **持ち主は screen-list**。ID を発行するのは screen-list だけで、他のツールは参照するだけ
- 画面名ではなく、揺れにくい実装の場所から作る（例：`web/tasks/new`、ダイアログは `web/tasks#DeleteTaskDialog`）。画面名を付け直しても ID は変わらない
- 他のツールで画面を特定できないときは、推測せずに `[未解決: 画面を特定できない]` と書く

画面 ID でつながると、次の問いにツールをまたいで答えられる。

1. この画面はどのコードで実装されているか（screen-list → code-map）
2. この画面を確かめているテストはあるか（screen-list → test-steps、test-case-generator）
3. どのテストにも出てこない画面はどれか（テストの空白）

## update を流す順番

ソースが変わったら、入力になる側から順に update する。

1. `/qa-tools:code-map update`
2. `/qa-tools:screen-list update`
3. `/qa-tools:test-steps update`
4. `/qa-tools:test-priority update`

各ツールは update の前に、`inputs` に記録した入力の manifest と、今の入力の manifest を比べる。入力のほうが新しければ、その旨を伝えてから進める。古い入力のまま黙って作り直さない（原則 7）。

## 対象外

ヘルプ記事などの外部ドキュメントは、どのツールの入力にもしない。画面の有無も名前も、ソースコードだけから決める。

## 役割を混ぜないこと

「今回の変更で、どのテストまで流すか」（変更 → 画面 → テスト）は、code-map と screen-list で範囲を絞る仕事である。テストケースごとに重要度と規模を決める test-priority とは役割を分け、1 つのツールに混ぜない。
