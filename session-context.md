# セッション・コンテキスト

## 現在の進捗
* **第 4 章「基本のインタプリタ」完了**:
  * `0401_ident` 〜 `0416_escape`（全 16 節）の実装、テスト、原稿ドラフト、差分（`diff.txt`）のレビューが完了。
  * `0416_escape` にて `hello, world` の実行まで到達。
* **第 5 章「辞書」完了**:
  * `0501_dict` 〜 `0506_defclass`（全 6 節）の実装、テスト、原稿ドラフト、差分（`diff.txt`）のレビューが完了。
  * 辞書リテラル、ドット記法（プロパティアクセス・代入）、UFCS（パイプライン呼び出し）、メソッド記法（Bound Method / `self` チェック）、クラス構文糖衣（`defclass` / `defmethod`）を実装。
  * `0506_defclass` にて全 52 件のテストがパス。
  * 全節の `diff.txt` が `./book/generate_diffs.sh`（`diff -U 20`）と同期済み。
  * Zenn 原稿（`020500.c5-dict.md` 〜 `020506.c5-defclass.md`）のレビュー・修正が完了。

## 保留中・次回以降のタスク
1. **第 5 章コードのコミット**:
   * `book/0505_method_notation` および `book/0506_defclass` のコミット（またはサンプルコードリポジトリへの反映準備）。
2. **第 6 章「パターンマッチ」の着手**:
   * `docs/book-outline.md` および `020600.c5-pattern-match.md` に沿った第 6 章の実装（rest 引数 `[a, *rest]`、タプル・辞書のマッチ、分割代入、`match` 構文など）。

## AIへの申し送り事項（注意点）
* **「RCEPL」は造語でありタイポではない**: 第 3 章の中間コード式インタプリタ用ループ（Read-Compile-Execute-Print Loop）を表す Toil 独自の用語。REPL への修正を指摘・提案しないこと。
* **第 2 部における ICI（コンパイラ/VM）の非互換許容**: 第 2 部は TWI の拡張に専念するため、パーサが生成する新しい AST に Compiler や VM が未対応で実行時エラーになってもバグとして指摘しないこと（第 5 部で追従）。
* **構文糖衣のパーサ実装パターン**: `def`、`defclass`、`defmethod` などの識別子チェックは `case (Ident() as ident, params):` および `case Ident() as ident:` の形式を用い、不正な構文（数値等）に対して Python 側の `AttributeError` ではなく Toil の構文エラー assert が飛ぶようにすること。
* **束縛オブジェクトのタグ名**: UFCS およびメソッド記法で関数とターゲット値を束縛するタグには `(Ident("binding"), [func_val, target_val])` を使用すること。
* **差分の自動更新**: 差分更新時は `./book/generate_diffs.sh` を使用して `diff -U 20` 形式で生成すること。
