# CLAUDE.md

このリポジトリ（qa-tools プラグイン）を開発するエージェント向けのメモ。プラグインの使い方は [README.md](README.md) を参照。

## 構成と原則

- skill は `skills/<name>/SKILL.md`。frontmatter の `name` はディレクトリ名と一致させ、`description` は 1024 字以内（[Agent Skills 仕様](https://agentskills.io/specification)）
- SKILL.md は 500 行未満に保ち、詳細は `references/` に分ける。references は SKILL.md から 1 階層だけ参照する
- references の冒頭には `## 契約`（入力・出力・検査・次）を必ず置く
- 出力形式は `assets/` の雛形を正とし、references に雛形を重複させない
- 製品固有の値（チケット接頭辞・領域・ロール）を skill に書かない。利用側の `.qa/product.md` から読む
- ダミー製品のファイルには、冒頭にダミーである旨の注記を入れる

## コマンド

- テスト：`python3 -m unittest discover -s tests -t .`（標準ライブラリのみ。pytest は使わない）
- マニフェスト検証：`claude plugin validate .`
- 図の再生成（HTML は git 管理外。README・PR には PNG を使う）：`node ~/.claude/skills/archify/bin/archify.mjs finalize <type> docs/architecture/<name>.<type>.json docs/architecture/<name>.html --quality showcase --json`

## 配布

- 自分の他のプロジェクトで使うためだけに `marketplace.json` を置いている。公開マーケットプレイスには出さない
- ローカルパスで追加したプラグインは clone を直接読む（`claude plugin list --json` の `readFromFolder`）。バージョンを上げなくても編集は次のセッションで反映される

## E2E で試すとき

- `--plugin-dir` で読み込んだプラグインのディレクトリ配下には書き込めない。`examples/dummy-product` はプラグインの外にコピーしてから実行する
- 例：`claude -p "/qa-tools:test-case-generator PBI: DUMMY-001" --plugin-dir <repo> --permission-mode acceptEdits --output-format json`、ゲートの合図は `--resume <session_id>` で送る

## 変更するとき

- 検査スクリプトはテストを先に書く（`tests/fixtures/` に再現用の Markdown を置く）
- フローやゲートを変えたら、`docs/architecture/` の図と `skills/test-case-generator/evals/evals.json` も更新する
