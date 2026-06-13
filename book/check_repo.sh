#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$(cd "$SCRIPT_DIR/../../" && pwd)/toil-book"

if [ ! -d "$DEST_DIR/.git" ]; then
    echo "エラー: $DEST_DIR にGitリポジトリが見つかりません。"
    echo "先に build_repo.sh を実行してください。"
    exit 1
fi

cd "$DEST_DIR"
echo "【コミット履歴】"
git log --oneline --graph --all
echo ""
echo "【タグ一覧】"
git tag
