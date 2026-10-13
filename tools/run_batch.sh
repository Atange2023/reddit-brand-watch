#!/bin/bash
# usage: run_batch.sh <last30days_src_dir> <batch_dir> <from_line> <to_line>
# Runs lines [from,to] of <batch_dir>/queries.tsv (id<TAB>query<TAB>subreddits) in parallel, foreground.
SRC="$1"; B="$2"; FROM="$3"; TO="$4"
export UV_LINK_MODE=copy
one() {
  IFS=$'\t' read -r id q subs <<< "$1"
  cd "$SRC/skills/last30days" || exit 1
  timeout 160 uv run --python 3.12 scripts/last30days.py "$q" --search reddit --subreddits "$subs" \
    --days "${DAYS:-30}" --no-browser-cookies --emit md --output "$B/$id.md" --save-dir "$B/save" > "$B/$id.log" 2>&1
  echo "$id rc=$?" >> "$B/done.txt"
}
export -f one; export SRC B DAYS
sed -n "${FROM},${TO}p" "$B/queries.tsv" | tr '\n' '\0' | timeout 170 xargs -0 -P4 -I{} bash -c 'one "$@"' _ {}
tail -n 8 "$B/done.txt"
