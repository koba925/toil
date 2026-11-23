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
* **第 6 章「パターンマッチ」完了（第 2 部完了）**:
  * `0601_list_pattern` 〜 `0612_exception`（全 12 節）の実装、テスト、原稿、差分（`diff.txt`）のレビューが完了。
  * リストパターン（rest・分割代入・ワイルドカード）、`match` 式、ガード、リテラルパターン、タプルパターン、辞書パターン、型パターン、OR パターン（`|`）、モジュール（`load` / `util.toil`）、アロー関数（`->`）、例外処理（`try` / `catch` / `raise`）を実装。
  * `0612_exception` にて全 64 件のテストがパス。第 6 章全 12 節で `toil.py` 実行・`pytest`・`diff.txt` 同期・88 文字制限チェック済み。
  * Zenn 原稿（`020600.c6-pattern-match.md` 〜 `020612.c6-exception.md`、`020000.p2-expanding-twi.md`、`config.yaml`）のレビュー・`textlint`（エラー 0 件）・GitHub リンク検証が完了。

## 保留中・次回以降のタスク
1. **第 6 章の最終コミット・公開作業**:
   * 未追跡の `book/0612_exception/` のコミット。
   * 必要に応じて `book/build_repo.sh` / `check_repo.sh` / `push_repo.sh` による `toil-book` 更新と Zenn 原稿の公開。
2. **第 3 部「メタサーキュラー構造（セルフ実行）」の着手**:
   * `docs/book-outline.md` に沿った `eval` / `eval_expr` / `apply` の追加およびセルフインタプリタ（Toil on Toil）の設計・実装。

## AIへの申し送り事項（注意点）
* **「RCEPL」は造語でありタイポではない**: 第 3 章の中間コード式インタプリタ用ループ（Read-Compile-Execute-Print Loop）を表す Toil 独自の用語。REPL への修正を指摘・提案しないこと。
* **第 2 部における ICI（コンパイラ/VM）の非互換許容**: 第 2 部は TWI の拡張に専念するため、パーサが生成する新しい AST に Compiler や VM が未対応で実行時エラーになってもバグとして指摘しないこと（第 5 部で追従）。
* **構文糖衣のパーサ実装パターン**: `def`、`defclass`、`defmethod` などの識別子チェックは `case (Ident() as ident, params):` および `case Ident() as ident:` の形式を用い、不正な構文（数値等）に対して Python 側の `AttributeError` ではなく Toil の構文エラー assert が飛ぶようにすること。
* **束縛オブジェクトのタグ名**: UFCS およびメソッド記法で関数とターゲット値を束縛するタグには `(Ident("binding"), [func_val, target_val])` を使用すること。
* **差分の自動更新**: 差分更新時は `./book/generate_diffs.sh` を使用して `diff -U 20` 形式で生成すること。
* **`util.toil` の引き継ぎ**: `0610_module` 以降、`gcd.toil` と同様に `util.toil` も後続節ディレクトリへコピーする。
* **第 6 章で確立した主な設計・仕様**:
  * OR パターンは将来のマクロ展開（第 4 部）と衝突しないよう `or` ではなく `|` を使う。
  * `Scanner._two_char_operator(self, successors)` は今後の 2 文字演算子追加を見据えた共通化。
  * Python の文（`with` 等）が必要で `lambda` に収まらない組み込み関数（`_load`）は、`Interpreter` のメソッドを増やさず `_builtins()` 内のローカル関数として定義する。
  * `raise` は引数 1 つ必須（`raise(val)`）とし、未捕捉の `ToilException` は `Interpreter.eval()` で捕捉して `assert False, f"Unhandled exception @ eval(): {e.val}"` に変換する。
  * `ToilException` の値属性は `ReturnException` と揃え `self.val`、`Parser._try()` の各節は `_match()` と揃えタプル `(exc_pat, exc_expr)` とする。
