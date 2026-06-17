#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get all chapter directories sorted
dirs=($(find . -mindepth 1 -maxdepth 1 -type d -name "[0-9]*" | sort))

prev_dir=""

for curr_dir in "${dirs[@]}"; do
    if [ -n "$prev_dir" ]; then
        curr_basename=$(basename "$curr_dir")
        if [[ "$curr_basename" > "0102" ]]; then
            if [ -f "$prev_dir/toil.py" ] && [ -f "$curr_dir/toil.py" ]; then
                echo "Generating diff: $prev_dir -> $curr_dir"
                # diff exits with 1 when differences are found, so we add "|| true" to prevent the script from stopping
                diff -U 20 "$prev_dir/toil.py" "$curr_dir/toil.py" > "$curr_dir/diff.txt" || true
            else
                echo "Skipping diff: toil.py not found in $prev_dir or $curr_dir"
            fi
        else
            echo "Skipping diff for $curr_basename (manual edit preserved)"
        fi
    fi
    prev_dir="$curr_dir"
done

echo "Diff generation complete."
