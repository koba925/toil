# toil-book

## このリポジトリについて

このリポジトリは、Zenn にてドラフト版公開中の『育てて学ぶ はじめての自作プログラミング言語』（仮題）のためのソースコードです。

* 『[育てて学ぶ はじめての自作プログラミング言語 Book 1](https://zenn.dev/kb84tkhr/books/learning-by-growing-language)』
* 『[育てて学ぶ はじめての自作プログラミング言語 Book 2](https://zenn.dev/kb84tkhr/books/learning-by-growing-language-bk2)』

言語処理系が成長していく過程を、Git のタグを使って簡単に追うことができます。節ごとにタグが打ってありますので、GitHub の「Tags」で見たい節のタグ（例：0101_constants）を選択してください。

現在は「第 4 章　基本のインタプリタ」までを公開しており、対応するソースコードが参照可能です。第 1 部で作成した最小のインタプリタ（[0312_examples](https://github.com/koba925/toil-book/tree/0312_examples)）は 500 行程度の Python でツリーウォーク式インタプリタと中間コード＋仮想マシンによるインタプリタの両方が体験できるのがちょっと自慢です。

## サンプルコード

たとえば以下のようなコードが実行できます。

```
def factorial_iter(n) do
    result := 1;
    while n > 0 do
        result = result * n;
        n = n - 1
    end;
    result
end
```

その他の実行例については [0312_examples/toil.py](https://github.com/koba925/toil-book/blob/0312_examples/toil.py#L520) の下部、`# Example` のコメント以下をご覧ください。
`None` と `bool` と `int` しかなくて配列もタプルも辞書もクラスもないのになぜか二分探索木まで実装できています。ふしぎ！

第 4 章以降では、このインタプリタにいろいろと機能を追加していきます。

## ⚠️ 注意事項
リポジトリを clone しておくと任意の節のソースを手元で表示・実行できて便利ですが、ひとつ注意事項があります。このリポジトリは、執筆の都合上、ソースに変更があった場合**予告なく履歴の書き換え（Force Push）を行います**。そのため後日 pull するとコンフリクト（競合）エラーが発生する可能性があります。更新したいときには再度 clone からやりなおすことをお勧めします。
「Download ZIP」であればそのような心配はありませんが、節ごとにダウンロードする必要があります。

