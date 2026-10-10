# skill の書き方の基準

qa-tools の skill（`skills/<ツール名>/`）を書くとき・レビューするときの基準。Anthropic が公開している [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) と [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) を、qa-tools の約束（[principles.md](principles.md)）に当てはめたもの。

「テスト」の列は、その基準を守れていないとテストが失敗するもの。空欄は、レビューで見る。

## 基準

| # | 基準 | qa-tools での決め方 | テスト |
| --- | --- | --- | --- |
| S1 | `name` は 64 字以内の小文字・数字・ハイフン。`description` は 1024 字以内で、何をするか と いつ使うか の両方を書く | `description` に、ユーザーが実際に言いそうな言い方（例：「変わったケースだけ判定し直して」）を入れる | `test_skill_structure` |
| S2 | SKILL.md の本文は 500 行未満 | 詳細は `references/` に分ける | `test_skill_structure` |
| S3 | 参照は SKILL.md から 1 階層まで。reference 同士が指し合わない | すべての reference を SKILL.md の表からリンクする。reference の中で「別の reference の手順 N と同じ」と書かず、手順をその場に書く | `test_skill_structure`、`test_priority_platform` |
| S4 | 実行環境と依存を書く | SKILL.md に Python の版と、`pip install` が要らないことを書く。古い版では、スクリプトが最初に、分かるメッセージで止まる | `test_priority_platform` |
| S5 | スクリプトは失敗を引き受ける（AI に丸投げしない） | 終了コード 0 / 1 / 2 と、どのファイルの何行目かを含むメッセージ。スタックトレースを出さない | `test_priority_pipeline` |
| S6 | 決まった処理はスクリプト、意味の判断だけ AI（低い自由度と高い自由度を使い分ける） | P3。AI の下書きは、スクリプトが検査してから取り込む（作る → 検証 → 実行） | `test_priority_pipeline` |
| S7 | 例を 3〜5 個、`<example>` で包んで示す。多様にする | AI が判断する基準（意味の判断）には、必ず例を付ける。正常系・異常系・見た目だけ・権限、のように散らす | レビュー |
| S8 | 指示には理由を添える。「〜するな」より「〜せよ」 | 禁止だけを並べず、理由か、代わりにすることを書く（例：「Write で書く。内容が人に見え、取り込む前に確認できる」） | レビュー |
| S9 | 用語を統一する | glossary.md にある言葉だけを使う。AI の仕事（判断）とスクリプトの仕事（決定）のように、近い言葉は SKILL.md の「言葉」の表で使い分けを書く | レビュー |
| S10 | 複雑な手順は、コピーして使えるチェックリストにする | `build` `update` の先頭に、進み具合のチェックリストを置く | レビュー |
| S11 | `<skill>` のような置き換え記号は、最初に定義する | 「`<skill>` は、この SKILL.md があるディレクトリ」と書く | レビュー |
| S12 | 評価（evals）を 3 つ以上書き、実際に動かす。複数のモデルで試す | 評価ごとに、期待する動き（`expectations`）を書く。動かして期待が実際と違えば、評価を直す。Haiku・Sonnet・Opus で 1 回ずつ動かす | レビュー（結果は PR に書く） |
| S13 | 時間とともに古くなる情報を書かない | 「まだ無い」「今は未実装」を SKILL.md に書かない（仕様書の状態欄には書いてよい） | レビュー |
| S14 | 仮の値には理由を書く（理由の無い定数を置かない） | P9。測っていない値は「仮」と書き、見直し方を書く | レビュー |

## 動かして確かめるとき

評価を `claude -p` で動かす。`--model` でモデルを変える。

```bash
claude -p "<評価の prompt>" --model haiku --plugin-dir <このリポジトリ> --permission-mode acceptEdits --allowedTools "Bash(python3:*)" --output-format json
```

動かしたあとは、出力のファイルと、報告の文章の両方を、評価の `expectations` と見比べる。
