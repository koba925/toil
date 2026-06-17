#!/bin/bash
set -e

# スクリプトのあるディレクトリを基準に絶対パスを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"
# toilリポジトリの隣（外側）に作成する
DEST_DIR="$(cd "$SCRIPT_DIR/../../" && pwd)/toil-book"

echo "toil-book リポジトリの構築を開始します..."

# 出力先ディレクトリの初期化
if [ -d "$DEST_DIR" ]; then
    echo "既存の '$DEST_DIR' を削除しています..."
    rm -rf "$DEST_DIR"
fi

mkdir -p "$DEST_DIR"

# Gitリポジトリの初期化
cd "$DEST_DIR"
git init
git checkout -b main 2>/dev/null || git branch -M main
cd - > /dev/null

# bookディレクトリ内の章フォルダを取得（名前が数字から始まるフォルダを辞書順に処理）
for CHAP_DIR in $(find "$SOURCE_DIR" -mindepth 1 -maxdepth 1 -type d -name "[0-9]*" | sort); do
    TAG_NAME=$(basename "$CHAP_DIR")
    echo "処理中: $TAG_NAME"

    # rsyncを使って同期（不要なキャッシュファイルなどは除外）
    rsync -a --delete \
        --exclude '.git/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude '.pytest_cache/' \
        --exclude '.DS_Store' \
        --exclude 'diff.txt' \
        "$CHAP_DIR/" "$DEST_DIR/"

    # 共通のREADMEファイルがあれば配置する
    if [ -f "$SOURCE_DIR/README.md" ]; then
        cp "$SOURCE_DIR/README.md" "$DEST_DIR/README.md"
    fi

    # DEST_DIR に移動してGit操作
    cd "$DEST_DIR"

    git add .

    if ! git diff --cached --quiet; then
        git commit -m "Step: $TAG_NAME"
        git tag "$TAG_NAME"
    else
        echo "  -> 変更がありませんでした（スキップ）"
    fi

    cd - > /dev/null
done

echo ""
echo "🎉 ローカルリポジトリの構築が完了しました！"
echo "場所: $DEST_DIR"
