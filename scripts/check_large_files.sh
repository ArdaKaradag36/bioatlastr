#!/usr/bin/env bash
# Fails when a tracked or staged file is larger than 20 MB (GitHub warns at 50 MB, blocks at 100 MB).
cd "$(dirname "$0")/.."
big=$(git ls-files -z | xargs -0 du -b 2>/dev/null | awk '$1 > 20*1024*1024 {print $2" ("$1" bytes)"}')
[ -z "$big" ] && { echo "no tracked file > 20 MB"; exit 0; }
echo "TOO LARGE:"; echo "$big"; exit 1
