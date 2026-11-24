# セッション・コンテキスト

## 現在の進捗
* **第 1 部（Book 1: 第 1〜3 章）**: 完了・公開済み。
* **第 2 部（Book 2: 第 4〜6 章 / `0401_ident`〜`0612_exception` 全 34 節）**: 完了・横断レビュー・同期・コミット済み。
  * 実装・テスト（`0612_exception` で 64 件パス）・原稿（全 38 ファイル）・`diff.txt`・ローカル `toil-book`（`0612_exception` まで）すべて同期済み。
  * 第 5〜6 章の Toil 文字列リテラルを `'...'`（エスケープ不要時）へ統一済み。
  * 全 34 節で `toil.py` 実行・`pytest`・88 文字制限・`textlint`（エラー 0 件）を確認済み（`toil`: `f7f86ef`、`zenn-content`: `4b4cc87`）。

## 次回以降のタスク
1. **公開作業（未実施分があれば）**: 必要に応じて `book/push_repo.sh` で GitHub（`toil-book`）へタグ反映・リンク疎通確認。
2. **第 3 部「メタサーキュラー構造（セルフ実行）」の着手（Book 2 に追記）**: `docs/book-outline.md` に沿った `eval` / `eval_expr` / `apply` の追加およびセルフインタプリタ（Toil on Toil）の設計・実装。

## AI への申し送り事項（設計前提）
* **束縛オブジェクトのタグ名**: UFCS・メソッド記法の束縛値は `(Ident("binding"), [func_val, target_val])`。
* **OR パターンの記号**: 将来のマクロ展開（第 4 部）と衝突しないよう `or` ではなく `|` を使用。
* **2 文字演算子の共通化**: `Scanner._two_char_operator(self, successors)` は今後の 2 文字演算子追加を見据えた共通化。
* **複雑な組み込み関数の定義位置**: Python の文（`with` 等）が必要で `lambda` に収まらない組み込み関数（`_load` 等）は `Interpreter` のメソッドを増やさず `_builtins()` 内のローカル関数として定義する。
* **例外処理の仕様**: `raise` は引数 1 つ必須（`raise(val)`）、未捕捉の `ToilException` は `Interpreter.eval()` で `assert False, f"Unhandled exception @ eval(): {e.val}"` に変換。`ToilException` の値属性は `self.val`、`Parser._try()` の各節はタプル `(exc_pat, exc_expr)`。
