#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$(cd "$SCRIPT_DIR/../../" && pwd)/toil-book"
GITHUB_URL="https://github.com/koba925/toil-book.git"

if [ ! -d "$DEST_DIR/.git" ]; then
    echo "エラー: $DEST_DIR にGitリポジトリが見つかりません。"
    echo "先に build_repo.sh を実行してください。"
    exit 1
fi

cd "$DEST_DIR"

echo "GitHub ($GITHUB_URL) へプッシュしています..."

# リモートがなければ追加、あればURL変更
if git remote | grep -q "^origin$"; then
    git remote set-url origin "$GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
fi

git push -f origin main
git push origin --prune 'refs/tags/*'


echo "🎉 プッシュが完了しました！ URL: https://github.com/koba925/toil-book"
