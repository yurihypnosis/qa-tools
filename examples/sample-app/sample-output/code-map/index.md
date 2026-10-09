# モジュール一覧

| モジュール | ファイル数 | 公開シンボル数 | 概要 | 詳細 |
| --- | --- | --- | --- | --- |
| (root) | 1 | 2 | ルート直下にある、アプリ全体に効く設定的なファイルを置く。 | [modules/(root).md](modules/%28root%29.md) |
| app | 1 | 3 | アプリ全体のHTMLの土台（文書の言語、フォントの読み込み、ビューポート、メタ情報）を作るルートレイアウトを置く。 | [modules/app.md](modules/app.md) |
| app/(auth) | 3 | 3 | ログインと新規登録の画面を置く。 | [modules/app__(auth).md](modules/app__%28auth%29.md) |
| app/(main) | 18 | 29 | ログイン後の画面（ダッシュボード、問題集一覧、単語カード、ロードマップ、学習ログ、思考フレーム、コードの読み方など）を置く。 | [modules/app__(main).md](modules/app__%28main%29.md) |
| app/api | 2 | 3 | ブラウザから呼ばれる API ルートを置く。 | [modules/app__api.md](modules/app__api.md) |
| features/code-tour | 2 | 14 | 「コードの読み方」ガイドの内容を置く。 | [modules/features__code-tour.md](modules/features__code-tour.md) |
| features/flashcards | 9 | 26 | 単語カード機能を置く。 | [modules/features__flashcards.md](modules/features__flashcards.md) |
| features/g-kentei-cheatsheet | 2 | 4 | G検定のチートシート（要点を一覧にしたもの）の型と表示画面を置く。 | [modules/features__g-kentei-cheatsheet.md](modules/features__g-kentei-cheatsheet.md) |
| features/mindset | 1 | 4 | 勉強の考え方（逆算、回転数、アウトプット重視など）を並べる読み物を置く。 | [modules/features__mindset.md](modules/features__mindset.md) |
| features/quiz | 32 | 134 | 問題集の演習機能の中心を置く。 | [modules/features__quiz.md](modules/features__quiz.md) |
| features/roadmap | 1 | 10 | 学習ロードマップ（フェーズと項目）のデータモデルと既定の内容を置く。 | [modules/features__roadmap.md](modules/features__roadmap.md) |
| shared/components | 1 | 4 | 全画面で共通のアプリの枠（サイドバー、トップバー、問題集の切り替え）を置く。 | [modules/shared__components.md](modules/shared__components.md) |
| shared/lib | 4 | 6 | Supabase への接続の窓口（ブラウザ用、サーバー用、ミドルウェア用）と、小さな共通関数を置く。 | [modules/shared__lib.md](modules/shared__lib.md) |
| types | 1 | 5 | データベースの表と関数の型定義を一か所に集めて置く。 | [modules/types.md](modules/types.md) |
