---
name: book
description: Toil を題材にした書籍に関するディレクトリ構成やルールを確認する際に自動ロードする
trigger: model_decision
---
Toil を題材とした書籍「[育てて学ぶ はじめての自作プログラミング言語](https://zenn.dev/kb84tkhr/books/learning-by-growing-language)」を執筆中（第 1 部・第 2 部完了、第 3 部へ進行中）。

## コンセプトとターゲット
* 厳密さよりも楽しさ・わかりやすさを優先し、スモールステップで動かして達成感を得ながら処理系の作り方を学べる構成にする。
* ターゲットは「Python の基礎（リスト、辞書、クラス）は知っているが、言語処理系は初めて」の読者。説明の飛躍や急な難易度上昇を避け、一度に多すぎる概念を導入しない。

## 書籍用ソースコードとテスト
* `book/<mmnn_xxx>/` に節ごとの完全なソースコードを配置（`mm`: 章、`nn`: 節、`xxx`: 内容。例: `0101_constants`）。
  * `toil.py`: 処理系本体
  * `test_eval.py` / `test_twi.py` / `test_ici.py`: 評価器 / TWI / ICI のテスト（実行は `.venv/bin/pytest`）
  * `diff.txt`: 前節の `toil.py` との差分
  * `gcd.toil`・`util.toil`: 付随サンプル（`util.toil` は `0610_module` 以降、後続節へ引き継ぐ）
* プロジェクトルートの `toil_final.py` 等は試作品。書籍の流れ上書き換えている箇所はあるが、テスト漏れ確認等に参照可。
* `book/draft.md` は執筆ネタメモ。タイポ・誤りや興味深いトピックの提案は随時歓迎（体裁の指摘は不要）。

## 読者向けサンプルコード（`toil-book`）
* 公開先: https://github.com/koba925/toil-book（`book/<mmnn_xxx>` をタグ化）。
* 操作スクリプト: `book/build_repo.sh`（ローカル構築）、`book/check_repo.sh`（タグ確認）、`book/push_repo.sh`（GitHub へ強制 push）。
* 読者へのタグ切替案内は、初級者が detached HEAD で迷子になるのを防ぐため GitHub Web UI（Tags ドロップダウン）での閲覧を基本とする。

## 書籍の原稿（`<ZENN>` = `~/projects/zenn-content`）
* `<ZENN>/books/learning-by-growing-language`: Book 1（第 1 部、公開済み）。
* `<ZENN>/books/learning-by-growing-language-bk2`: Book 2（第 2 部完了・公開済み、第 3 部も続けて追記予定）。

## パート（部）ごとの開発方針
* **実装計画の確認**: 現在位置や次の実装に迷った場合は必ず `docs/book-outline.md` を参照し、推測で進めない。
* **第 2 部（第 4〜6 章、`0403` 以降）**: TWI の機能拡張に専念するため `test_ici.py` は含めず、ICI（Compiler / VM）は修正しない。新しい AST に Compiler / VM が未追従で `run()` 等がクラッシュしても意図的な仕様であり、指摘・修正提案しない（第 5 部で追従）。
* **コンテキスト・ルールの維持**: 本ファイル・`session-context.md`・他ルール（`coding-style.md` / `policy.md` / `review.md`）は役割を重複させず、完了済みログを削りながら常にコンパクトに保つ。
