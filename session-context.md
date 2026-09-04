# セッション・コンテキスト

## 現在の進捗
* 第4章の機能追加 `book/0401_ident` （Identクラスの導入）の実装とレビューが完了した。
* 構成案が肥大化したため、`README.md` から `docs/book-outline.md` に書籍のアウトラインを分離した。

## 開発環境とツールの状態
* **テスト実行**: `book.md` のルール通り、必ず `.venv/bin/pytest` または `run_tests.sh` を使用する。

## 保留中・次回以降のタスク
* **次フェーズの実装**: `docs/book-outline.md` に従い、次の言語機能（型ヒントの追加など）の実装に進む。

## AIへの申し送り事項（注意点）
* **ルールの絶対遵守**: `review-section-03-tests` や `04-final` を実行する際は、必ず事前に `.agents/rules/coding-style.md` と `.agents/rules/book.md` を読み込むこと。
* **内部構造のテスト強要禁止**: `coding-style.md` に記載の通り、`eval()`, `walk()`, `run()` のE2Eテストでカバーされている場合、`Ident`クラスのような内部構造に依存したテストの追加をユーザーに要求してはならない。
* **diff.txtの同期確認**: コード修正直後にレビューを行う際、`diff.txt` の更新が漏れていることが多いため、`book/generate_diffs.sh` の実行確認を行うこと。
